from abc import ABC, abstractmethod


class BaseProvider(ABC):

    @abstractmethod
    def get_products(self):
        """Fetch products from the external platform."""
        raise NotImplementedError

    @abstractmethod
    def get_inventory(self):
        """Fetch inventory from the external platform."""
        raise NotImplementedError

    @abstractmethod
    def get_orders(self):
        """Fetch orders from the external platform."""
        raise NotImplementedError

    @abstractmethod
    def update_inventory(self, external_variant_id, quantity):
        """Update inventory for an external variant."""
        raise NotImplementedError