"""Button platform for Nissan Leaf OBD BLE."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME
from .entity import NissanLeafObdBleEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NissanLeafObdBleRefreshButton(coordinator, entry)])


class NissanLeafObdBleRefreshButton(NissanLeafObdBleEntity, ButtonEntity):
    """Button that triggers an immediate coordinator refresh."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"
    _attr_name = f"{NAME} Refresh"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize the button."""
        super().__init__(coordinator, config_entry)

    async def async_press(self) -> None:
        """Trigger an immediate update."""
        await self.coordinator.async_request_refresh()
