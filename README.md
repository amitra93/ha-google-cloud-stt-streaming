# Google Cloud Speech-to-Text V2 for Home Assistant

Custom Home Assistant integration that exposes Google Cloud Speech-to-Text V2
streaming recognition as an STT entity.

## Installation

1. Copy `custom_components/google_cloud_stt_v2` into the `custom_components`
   directory of your Home Assistant configuration.
2. Restart Home Assistant.
3. Open **Settings > Devices & services**, select **Add integration**, and
   choose **Google Cloud Speech-to-Text V2**.
4. Upload or paste a Google Cloud service-account JSON key, then select the
   region and model.

Enable the Google Cloud Speech-to-Text V2 API and grant the service account
permission to use it before configuring the integration.

The service-account JSON is stored in the Home Assistant config entry. Never
commit a credential file or paste credential contents into this repository.

## Supported Features

- Google Cloud Speech-to-Text V2 streaming recognition
- Interim and final transcript events on the Home Assistant event bus
- Configurable recognizer, model, region, phrase hints, punctuation, and
  voice-activity timeouts
- Home Assistant STT capability metadata for WAV/PCM and OGG/Opus input

## Requirements

The integration declares its Python dependency in
`custom_components/google_cloud_stt_v2/manifest.json`.

## Documentation

Repository: https://github.com/amitra93/ha-google-cloud-stt-streaming
