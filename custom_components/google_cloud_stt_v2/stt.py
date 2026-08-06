"""Support for Google Cloud Speech-to-Text V2 service."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterable
import logging
import re
from typing import override

from google.api_core.exceptions import GoogleAPIError
from google.api_core.retry import AsyncRetry
from google.cloud.speech_v2 import SpeechAsyncClient, types
from google.protobuf import duration_pb2
from propcache.api import cached_property

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechAudioProcessing,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_PHRASE_HINTS,
    CONF_PUNCTUATION,
    CONF_RECOGNIZER,
    CONF_REGION,
    CONF_SERVICE_ACCOUNT_INFO,
    CONF_SPEECH_END_TIMEOUT,
    CONF_SPEECH_START_TIMEOUT,
    DEFAULT_PUNCTUATION,
    DEFAULT_SPEECH_END_TIMEOUT,
    DEFAULT_SPEECH_START_TIMEOUT,
    DOMAIN,
    EVENT_ERROR,
    EVENT_TRANSCRIPT,
    HA_TO_GCP_LANG_MAP,
    STT_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)

RECOGNIZER_PATTERN = re.compile(r"projects/([^/]+)/locations/([^/]+)/recognizers/([^/]+)")


def extract_location_from_recognizer(recognizer_path: str, default_location: str = "us-central1") -> str:
    """Extract location region from full GCP recognizer string."""
    m = RECOGNIZER_PATTERN.match(recognizer_path.strip())
    if m:
        return m.group(2)
    return default_location


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Google Cloud STT V2 entity via config entry."""
    service_account_info = config_entry.data[CONF_SERVICE_ACCOUNT_INFO]
    options = config_entry.options
    project_id = service_account_info.get("project_id", "")
    default_region = config_entry.data.get(CONF_REGION, "us-central1")

    recognizer_path = options.get(CONF_RECOGNIZER, config_entry.data.get(CONF_RECOGNIZER, "")).strip()
    if not recognizer_path:
        recognizer_path = f"projects/{project_id}/locations/{default_region}/recognizers/_"

    location = extract_location_from_recognizer(recognizer_path, default_region)

    client_options = None
    if location and location != "global":
        client_options = {"api_endpoint": f"{location}-speech.googleapis.com"}

    client = SpeechAsyncClient.from_service_account_info(
        service_account_info, client_options=client_options
    )
    async_add_entities([GoogleCloudV2SpeechToTextEntity(config_entry, client, recognizer_path, location)])


class GoogleCloudV2SpeechToTextEntity(SpeechToTextEntity):
    """Google Cloud STT V2 entity."""

    def __init__(
        self,
        entry: ConfigEntry,
        client: SpeechAsyncClient,
        recognizer_path: str,
        location: str,
    ) -> None:
        """Init Google Cloud STT V2 entity."""
        self._attr_unique_id = f"{entry.entry_id}"
        self._attr_name = entry.title
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Google",
            model="Cloud STT V2",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self._entry = entry
        self._client = client
        self._recognizer_path = recognizer_path
        self._location = location

    @cached_property
    @override
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        supported = set(STT_LANGUAGES)
        supported.update(HA_TO_GCP_LANG_MAP.keys())
        return sorted(supported)

    @property
    @override
    def supported_formats(self) -> list[AudioFormats]:
        """Return supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    @override
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    @override
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    @override
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return supported samplerates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    @override
    def supported_channels(self) -> list[AudioChannels]:
        """Return supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    @property
    @override
    def audio_processing(self) -> SpeechAudioProcessing:
        """Return audio processing settings.

        Set requires_external_vad=False so Home Assistant does NOT load local VAD (VoiceCommandSegmenter).
        """
        return SpeechAudioProcessing(
            requires_external_vad=False,
            prefers_auto_gain_enabled=True,
            prefers_noise_reduction_enabled=True,
        )

    @override
    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process audio stream to STT V2 service."""
        language_code = HA_TO_GCP_LANG_MAP.get(
            metadata.language, metadata.language
        )

        options = self._entry.options
        punctuation = options.get(CONF_PUNCTUATION, DEFAULT_PUNCTUATION)
        phrase_hints_str = options.get(CONF_PHRASE_HINTS, "")
        speech_start_timeout = options.get(CONF_SPEECH_START_TIMEOUT, DEFAULT_SPEECH_START_TIMEOUT)
        speech_end_timeout = options.get(CONF_SPEECH_END_TIMEOUT, DEFAULT_SPEECH_END_TIMEOUT)

        _LOGGER.warning(
            "Starting GCP STT V2 stream for recognizer=%s, lang=%s, sample_rate=%s, format=%s",
            self._recognizer_path, language_code, metadata.sample_rate, metadata.format
        )

        # Adaptation (phrase hints)
        adaptation = None
        if phrase_hints_str:
            phrases_list = [p.strip() for p in phrase_hints_str.split(",") if p.strip()]
            if phrases_list:
                adaptation = types.SpeechAdaptation(
                    phrase_sets=[
                        types.SpeechAdaptation.AdaptationPhraseSet(
                            inline_phrase_set=types.PhraseSet(
                                phrases=[types.PhraseSet.Phrase(value=p, boost=10.0) for p in phrases_list]
                            )
                        )
                    ]
                )

        config_kwargs = {
            "explicit_decoding_config": types.ExplicitDecodingConfig(
                encoding=types.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=metadata.sample_rate,
                audio_channel_count=1,
            ),
            "language_codes": [language_code],
            "adaptation": adaptation,
            "features": types.RecognitionFeatures(
                enable_automatic_punctuation=punctuation,
            ),
        }

        if self._recognizer_path.endswith("/_"):
            model = self._entry.data.get(CONF_MODEL, "chirp_2")
            config_kwargs["model"] = model

        recognition_config = types.RecognitionConfig(**config_kwargs)

        vat = types.StreamingRecognitionFeatures.VoiceActivityTimeout(
            speech_start_timeout=duration_pb2.Duration(seconds=int(speech_start_timeout), nanos=int((speech_start_timeout % 1) * 1e9)),
            speech_end_timeout=duration_pb2.Duration(seconds=int(speech_end_timeout), nanos=int((speech_end_timeout % 1) * 1e9)),
        )

        streaming_config = types.StreamingRecognitionConfig(
            config=recognition_config,
            streaming_features=types.StreamingRecognitionFeatures(
                interim_results=True,
                enable_voice_activity_events=True,
                voice_activity_timeout=vat,
            ),
        )

        stop_stream = asyncio.Event()
        first_chunk = True
        chunk_count = 0
        total_bytes = 0

        async def request_generator() -> AsyncGenerator[types.StreamingRecognizeRequest]:
            nonlocal first_chunk, chunk_count, total_bytes
            _LOGGER.warning("Sending initial StreamingRecognizeRequest config for %s", self._recognizer_path)
            yield types.StreamingRecognizeRequest(
                recognizer=self._recognizer_path,
                streaming_config=streaming_config,
            )
            async for chunk in stream:
                if stop_stream.is_set():
                    _LOGGER.warning("Stopping audio request generator cleanly after is_final")
                    break

                chunk_count += 1
                total_bytes += len(chunk)

                # Strip 44-byte WAV header (RIFF) on first chunk if present
                if first_chunk:
                    first_chunk = False
                    if chunk.startswith(b"RIFF") and len(chunk) > 44:
                        _LOGGER.warning("Stripped 44-byte WAV header from first audio chunk (original size: %d)", len(chunk))
                        chunk = chunk[44:]

                yield types.StreamingRecognizeRequest(
                    recognizer=self._recognizer_path,
                    audio=chunk,
                )
            _LOGGER.warning("Audio stream source ended: %d chunks, %d total bytes", chunk_count, total_bytes)

        final_transcript = ""

        try:
            responses = await self._client.streaming_recognize(
                requests=request_generator(),
                timeout=30,
                retry=AsyncRetry(initial=0.1, maximum=2.0, multiplier=2.0),
            )

            async for response in responses:
                if not response.results:
                    continue

                for result in response.results:
                    if not result.alternatives:
                        continue

                    transcript_text = result.alternatives[0].transcript
                    is_final = result.is_final

                    _LOGGER.warning("GCP STT V2 TRANSCRIPT (is_final=%s): %s", is_final, transcript_text)

                    if is_final:
                        final_transcript = transcript_text.strip()
                        stop_stream.set()

                    # Stream event to Home Assistant bus
                    self.hass.bus.async_fire(
                        EVENT_TRANSCRIPT,
                        {
                            "is_final": is_final,
                            "transcript": transcript_text,
                            "engine_id": self.entity_id,
                        },
                    )

        except GoogleAPIError as err:
            err_msg = str(err).lower()
            if final_transcript or "operation was cancelled" in err_msg or getattr(err, "code", None) in (409, 499, 500):
                _LOGGER.warning("GCP STT V2 stream ended: final=%s (chunks: %d, bytes: %d)", final_transcript, chunk_count, total_bytes)
                return SpeechResult(final_transcript, SpeechResultState.SUCCESS)

            _LOGGER.error("Error during Google Cloud STT V2 call: %s", err)
            self.hass.bus.async_fire(
                EVENT_ERROR,
                {
                    "error": str(err),
                    "engine_id": self.entity_id,
                },
            )
            return SpeechResult(None, SpeechResultState.ERROR)
        except Exception as err:
            if final_transcript:
                _LOGGER.warning("GCP STT V2 stream ended after final transcript: %s", final_transcript)
                return SpeechResult(final_transcript, SpeechResultState.SUCCESS)

            _LOGGER.exception("Unexpected error during Google Cloud STT V2 call: %s", err)
            self.hass.bus.async_fire(
                EVENT_ERROR,
                {
                    "error": str(err),
                    "engine_id": self.entity_id,
                },
            )
            return SpeechResult(None, SpeechResultState.ERROR)

        _LOGGER.warning("STT finished cleanly with final transcript: %s", final_transcript)
        return SpeechResult(final_transcript, SpeechResultState.SUCCESS)
