"""Light platform for DreamScreen SideKick / HD / 4K devices."""
import logging

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TIMEOUT
import homeassistant.helpers.config_validation as cv

from .pydreamscreen import get_device, get_state

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 2

# name -> (device mode, ambient scene or None)
# modes: 0 off, 1 video, 2 music, 3 ambient
EFFECTS = {
    "Video": (1, None),
    "Music": (2, None),
    "Random": (3, 0),
    "Fire": (3, 1),
    "Twinkle": (3, 2),
    "Ocean": (3, 3),
    "Pride": (3, 4),
    "Fireworks": (3, 5),
    "Holiday": (3, 6),
    "Pop": (3, 7),
    "Forest": (3, 8),
}
EFFECT_BY_STATE = {v: k for k, v in EFFECTS.items()}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        # ponytail: bump if the device is slow to answer on a busy wifi
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(float),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a single DreamScreen device by IP."""
    host = config[CONF_HOST]
    timeout = config[CONF_TIMEOUT]

    state = get_state(ip=host, timeout=timeout)
    if not state:
        _LOGGER.error("No DreamScreen device answered at %s", host)
        return
    device = get_device(state)
    if device is None:
        _LOGGER.error("Unsupported DreamScreen device at %s: %s", host, state)
        return

    add_entities([DreamScreenLight(device, config.get(CONF_NAME), timeout)], True)


class DreamScreenLight(LightEntity):
    """A DreamScreen device as a light."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECTS)

    def __init__(self, device, name, timeout):
        """Wrap a pydreamscreen device."""
        self._device = device
        self._timeout = timeout
        self._attr_name = name or device.name
        self._attr_unique_id = "dreamscreen_{}".format(device.ip)

    def turn_on(self, **kwargs):
        """Set colour, effect and/or brightness, turning on if needed."""
        device = self._device

        if ATTR_RGB_COLOR in kwargs:
            device.mode = 3
            device.ambient_color = list(kwargs[ATTR_RGB_COLOR])
        elif ATTR_EFFECT in kwargs:
            mode, scene = EFFECTS[kwargs[ATTR_EFFECT]]
            device.mode = mode
            if scene is not None:
                device.ambient_scene = scene
        elif not self._attr_is_on:
            device.mode = 3

        if ATTR_BRIGHTNESS in kwargs:
            device.brightness = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)

    def turn_off(self, **kwargs):
        """Turn the LEDs off."""
        self._device.mode = 0

    def update(self):
        """Poll the device over UDP."""
        if not self._device.update_current_state(self._timeout):
            self._attr_available = False
            return

        device = self._device
        self._attr_available = True
        self._attr_is_on = device.mode != 0
        self._attr_brightness = round(device.brightness * 255 / 100)
        self._attr_rgb_color = tuple(device.ambient_color)
        self._attr_effect = EFFECT_BY_STATE.get(
            (device.mode, device.ambient_scene if device.mode == 3 else None)
        )
