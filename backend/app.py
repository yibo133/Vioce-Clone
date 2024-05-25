from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import torch
from TTS.api import TTS
import subprocess
import shutil

device = "cuda" if torch.cuda.is_available() else "gpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def convert_audio(input_path, output_path):
    command = [
        'ffmpeg',
        '-i', input_path,
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '2',
        output_path
    ]
    subprocess.run(command, check=True)

app = Flask(__name__)

UPLOAD_FOLDER = 'audio'
OUTPUT_FOLDER = 'outputs'
TEMPORARY = 'temporary'
ALLOWED_EXTENSIONS = {'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['TEMPORARY'] = TEMPORARY

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
global_text = None
@app.route('/api/set-text', methods=['POST'])
def set_text():
    global global_text
    data = request.get_json()
    global_text = data.get('text')
    if not global_text:
        return jsonify({'error': 'No text provided'}), 400
    return jsonify({'message': 'Text set successfully'}), 200
@app.route('/api/get-text')
def get_text():
    global global_text
    if global_text is None:
        return jsonify({'error': 'No text has been set'}), 404
    return jsonify({'text': global_text}), 200

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    if 'audioFile' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['audioFile']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    converted_filename = filename.rsplit('.', 1)[0] + '1.wav'
    output_path = os.path.join(UPLOAD_FOLDER, converted_filename)

    try:
        convert_audio(input_path, output_path)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Failed to convert audio', 'details': str(e)}), 500

    try:
        tts_output_path = os.path.join(OUTPUT_FOLDER, 'tts_output.wav')
        tts.tts_to_file(text=global_text, speaker_wav=output_path, language="en", file_path=tts_output_path)
        return jsonify({'audioUrl': f'/api/outputs/tts_output.wav'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/outputs/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        if os.path.exists(app.config['OUTPUT_FOLDER']):
            shutil.rmtree(app.config['OUTPUT_FOLDER'])
            os.makedirs(app.config['OUTPUT_FOLDER'])

        if os.path.exists(app.config['TEMPORARY']):
            shutil.rmtree(app.config['TEMPORARY'])
            os.makedirs(app.config['TEMPORARY'])
        
        return jsonify({"message": "Files cleared successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    if not os.path.exists(TEMPORARY):
        os.makedirs(TEMPORARY)
    app.run(host='0.0.0.0', port=5001)
