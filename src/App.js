import React, { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [text, setText] = useState('');
  const [recording, setRecording] = useState(false);
  const [audioChunks, setAudioChunks] = useState([]);
  const [audioUrl, setAudioUrl] = useState('');
  const [stream, setStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const audioPreviewRef = useRef(null);
  const ttsOutputRef = useRef(null);

  const handleTextChange = (e) => {
    setText(e.target.value);
  };

  const handleSubmitText = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/set-text', { text });
      alert(response.data.message);
    } catch (error) {
      console.error('Error setting text:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(stream);
      const mediaRecorder = new MediaRecorder(stream);
      setMediaRecorder(mediaRecorder);
      mediaRecorder.start();

      const chunks = [];
      mediaRecorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(audioUrl);
        audioPreviewRef.current.src = audioUrl;
        setAudioChunks(chunks);
      };

      setRecording(true);
    } catch (error) {
      console.error('Error accessing the microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      stream.getTracks().forEach((track) => track.stop());
      setRecording(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audioFile', audioBlob, 'filename.wav');

    try {
      const response = await axios.post('/api/upload-audio', formData);
      alert(response.data.message);
      ttsOutputRef.current.src = response.data.audioUrl;
    } catch (error) {
      console.error('Error uploading audio:', error);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
      const response = await axios.post('/api/upload-audio', formData);
      alert(response.data.message);
      ttsOutputRef.current.src = response.data.audioUrl;
    } catch (error) {
      console.error('Error uploading audio:', error);
    }
  };

  const clearFiles = async () => {
    try {
      const response = await axios.post('/api/clear-files');
      alert(response.data.message);
      setAudioUrl('');
      if (audioPreviewRef.current) audioPreviewRef.current.src = '';
      if (ttsOutputRef.current) ttsOutputRef.current.src = '';
    } catch (error) {
      console.error('Error clearing files:', error);
    }
  };

  return (
    <div className="container">
      <h1>Submit Text</h1>
      <form onSubmit={handleSubmitText}>
        <input type="text" value={text} onChange={handleTextChange} placeholder="Enter text here" required />
        <button type="submit">Submit Text</button>
      </form>

      <h1>Recording</h1>
      <button onClick={startRecording} disabled={recording}>Start Recording</button>
      <button onClick={stopRecording} disabled={!recording}>Stop Recording</button>
      <p>{recording ? 'Recording...' : 'Not Recording'}</p>
      <audio ref={audioPreviewRef} controls />

      <button onClick={handleUpload} disabled={!audioUrl}>Upload Recording</button>

      <h1>Upload Audio</h1>
      <form onSubmit={handleFileUpload}>
        <input type="file" name="audioFile" required />
        <button type="submit">Upload and Process</button>
      </form>

      <h1>Clone Live</h1>
      <audio ref={ttsOutputRef} controls src="/api/outputs/tts_output.wav"></audio>
      <button onClick={clearFiles}>Clear Files</button>
    </div>
  );
};

export default App;
