import os
import sys
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import tempfile
import pygame
from elevenlabs import generate, set_api_key  # Removed ElevenLabsError
from dotenv import load_dotenv
import threading
import re
import openai
import requests
import json
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all types of log messages
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
load_dotenv()
logging.debug("Environment variables loaded.")

# Check and set up API keys
OPENAI_API_KEY = os.getenv('LUNAS_OPENAI_API_KEY')
ELEVEN_LABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')
ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID', "asst_KjAIKMtL5ILTuqA1XRf0DcDK")

missing_vars = []
if not OPENAI_API_KEY:
    missing_vars.append('LUNAS_OPENAI_API_KEY')
if not ELEVEN_LABS_API_KEY:
    missing_vars.append('ELEVENLABS_API_KEY')
if not VOICE_ID:
    missing_vars.append('ELEVENLABS_VOICE_ID')

if missing_vars:
    logging.critical(f"Error: Missing environment variables: {', '.join(missing_vars)}.")
    sys.exit(1)

logging.debug("All required environment variables are set.")

# Set up OpenAI and Eleven Labs API keys
openai.api_key = OPENAI_API_KEY
set_api_key(ELEVEN_LABS_API_KEY)
logging.debug("API keys for OpenAI and Eleven Labs set.")

recording = None

# Define Pydantic models
class AssistantMessage(BaseModel):
    role: str
    content: str

class AssistantResponse(BaseModel):
    messages: Optional[list]

def play_audio_chunk(audio_chunk):
    try:
        pygame.mixer.init()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_chunk)
            temp_file_path = temp_file.name
            logging.debug(f"Temporary audio file created at {temp_file_path}.")

        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()
        logging.info("Playing audio chunk.")

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        os.unlink(temp_file_path)
        logging.debug(f"Temporary audio file {temp_file_path} deleted.")
    except Exception as e:
        logging.error(f"Error in play_audio_chunk: {e}")

def split_into_sentences(text):
    sentences = re.split('(?<=[.!?]) +', text)
    logging.debug(f"Split text into {len(sentences)} sentences.")
    return sentences

def group_sentences(sentences, max_chars=250):
    groups = []
    current_group = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) > max_chars and current_group:
            groups.append(' '.join(current_group))
            current_group = []
            current_length = 0
        current_group.append(sentence)
        current_length += len(sentence)

    if current_group:
        groups.append(' '.join(current_group))

    logging.debug(f"Grouped sentences into {len(groups)} chunks.")
    return groups

def process_and_play_chunks(text):
    try:
        sentences = split_into_sentences(text)
        chunks = group_sentences(sentences)

        for idx, chunk in enumerate(chunks, start=1):
            logging.debug(f"Processing chunk {idx}: {chunk}")
            audio_stream = generate(
                text=chunk,
                voice=VOICE_ID,
                model="eleven_multilingual_v2",
                stream=True
            )
            audio_chunk = b''.join(audio_stream)
            logging.debug(f"Generated audio for chunk {idx}.")
            play_audio_chunk(audio_chunk)
    except Exception as e:  # Changed from ElevenLabsError to Exception
        logging.error(f"Error in process_and_play_chunks: {e}")

def start_recording():
    global recording
    if recording is None:
        try:
            logging.info('Start recording...')
            recording = sd.rec(int(44100 * 50), samplerate=44100, channels=2, dtype='int16')
            logging.debug("Recording started.")
        except Exception as e:
            logging.error(f"Error starting recording: {e}")

def stop_and_process_recording():
    global recording
    if recording is not None:
        try:
            logging.info('Stop recording...')
            sd.stop()
            filename = 'recording.wav'
            sf.write(filename, recording, 44100)
            logging.debug(f"Recording saved to {filename}.")
            user_text = transcribe_audio(filename)
            os.remove(filename)
            logging.debug(f"Temporary recording file {filename} deleted.")
            recording = None
            return user_text
        except Exception as e:
            logging.error(f"Error stopping or processing recording: {e}")
    else:
        logging.warning("No recording to stop.")
    return None

def transcribe_audio(filename):
    try:
        logging.info(f"Transcribing audio from {filename}...")
        with open(filename, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        logging.debug(f"Transcription result: {transcript['text'].strip()}")
        return transcript["text"].strip()
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error during transcription: {e}")
    except Exception as e:
        logging.error(f"Error transcribing audio: {e}")
    return None

def send_to_openai(user_text):
    try:
        logging.info("Sending user text to OpenAI...")
        response = openai.ChatCompletion.create(
            model="o1-mini",  # Change to "o1-preview" if needed
            messages=[
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            max_completion_tokens=15000  # Adjust as needed
        )
        logging.debug(f"OpenAI response: {response}")

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content.strip()
        logging.info("Received response from OpenAI.")
        logging.debug(f"Assistant reply: {assistant_reply}")
        print(f"Assistant: {assistant_reply}")  # Ensure it's printed to console
        return assistant_reply

    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        print("Assistant: I'm sorry, I encountered an error while processing your request.")
        return "I'm sorry, I encountered an error while processing your request."
    except Exception as e:
        logging.error(f"Unexpected error in send_to_openai: {e}")
        print("Assistant: I'm sorry, an unexpected error occurred.")
        return "I'm sorry, an unexpected error occurred."

def save_response_to_file(response_text, user_text):
    try:
        user_input_words = user_text.split()[:3]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_name = f"{'_'.join(user_input_words)}_{timestamp}.txt"

        save_path = "responses"

        if not os.path.exists(save_path):
            os.makedirs(save_path)
            logging.debug(f"Created directory: {save_path}")

        full_path = os.path.join(save_path, file_name)
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(response_text)
        logging.info(f"Response saved to {full_path}.")
    except Exception as e:
        logging.error(f"Error saving response to file: {e}")

def process_recording():
    user_text = stop_and_process_recording()
    if user_text:
        logging.info(f"User said: {user_text}")
        print(f"You said: {user_text}")
        logging.info("Sending text to assistant.")
        print("Luna's response: ")
        openai_response_text = send_to_openai(user_text)

        if openai_response_text:
            # Use Pydantic model to parse the response
            try:
                assistant_message = AssistantMessage(role='assistant', content=openai_response_text)
                assistant_response = AssistantResponse(messages=[assistant_message.dict()])
                logging.debug("Assistant response parsed successfully.")
            except Exception as e:
                logging.error(f"Error parsing assistant response: {e}")
                assistant_response = AssistantResponse(messages=[{'role': 'assistant', 'content': "I'm sorry, I didn't understand that."}])

            # Extract content for playback
            response_content = assistant_response.messages[0]['content']
            save_response_to_file(response_content, user_text)
            process_and_play_chunks(response_content)

            print("\nReady to listen again! Hold Alt+X to record, release to process.")
            logging.info("Ready for next recording.")
        else:
            logging.warning("No response text received from OpenAI.")
            print("No response received. Please try again.")
    else:
        logging.warning("No speech detected or transcription failed. Please try again.")
        print("No speech detected or transcription failed. Please try again.")

def main_loop():
    logging.info("Application started. Luna is ready!")
    print("Luna is ready! Hold Alt+X to record, release to process.")

    keyboard.add_hotkey('alt+x', start_recording)
    keyboard.on_release_key('x', lambda _: process_recording(), suppress=True)

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        logging.info("Application terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unexpected error in main_loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_loop()
