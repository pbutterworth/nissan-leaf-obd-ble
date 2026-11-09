"""Button platform for Nissan Leaf OBD BLE."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import NissanLeafObdBleConfigEntry
from .entity import NissanLeafObdBleEntity

REFRESH_BUTTON = ButtonEntityDescription(
    key="refresh",
    name="Refresh",
    icon="mdi:refresh",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NissanLeafObdBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button platform."""
    async_add_entities(
        [NissanLeafObdBleRefreshButton(entry.runtime_data, REFRESH_BUTTON)]
    )


class NissanLeafObdBleRefreshButton(NissanLeafObdBleEntity, ButtonEntity):
    """Button that triggers an immediate coordinator refresh."""

    @property
    def available(self) -> bool:
        """Stay available so a failed poll can be retried by hand."""
        return True

    async def async_press(self) -> None:
        """Trigger an immediate update."""
        await self.coordinator.async_request_refresh()
