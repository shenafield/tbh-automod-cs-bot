from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Config:
    moderators: dict[str, float] = field(default_factory=dict)
    mod_message: Optional[int] = None


class ConfigReader(ABC):
    @abstractmethod
    def write_config(self, config: Config):
        pass

    @abstractmethod
    def read_config(self) -> Config:
        pass


class JsonConfigReader(ConfigReader):
    def __init__(self, path: str):
        self.path = path

    def write_config(self, config: Config):
        with open(self.path, "w") as f:
            json.dump(asdict(config), f, indent=4)

    def read_config(self) -> Config:
        with open(self.path) as f:
            return Config(**json.load(f))

