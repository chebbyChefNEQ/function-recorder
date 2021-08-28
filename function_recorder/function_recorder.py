import os
import pickle
import random
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union


@dataclass
class _FunctionRecorder:
    f: Callable
    sample_size: int
    save_path: Union[str, os.PathLike]

    _size: int = 0

    def _save_input(self, idx, *args, **kwargs):
        save_path = os.join(self.save_path, str(idx))
        with open(save_path, "wb") as f:
            pickle.dump(
                {
                    "args": args,
                    "kwargs": kwargs,
                },
                f,
            )

    def _reservoir_sample(self) -> Optional[int]:
        """Should sample -> return idx
        else -> return None
        """
        # Not full yet, keep filling
        if self._size < self.sample_size:
            idx = self._size
            self._size += 1
            return idx

        # Maybe replace
        k = random.randint(0, self.sample_size)
        if k < self.sample_size:
            return k

        # Don't replace
        return None

    def _f(self, *args, **kwargs):
        sample_idx = self._reservoir_sample()
        if sample_idx is not None:
            self._save_input(*args, **kwargs)
        return self.f(*args, **kwargs)


@dataclass
class _FunctionRecordingSystem:
    enabled = False or os.environ.get("FUNCTION_RECORDER_ENABLED", "false").lower() in {
        "true",
        "1",
        "on",
        "yes",
    }
    init_lock = threading.Lock()
    initalized = False
    save_path = f".function_recorder/{str(uuid.uuid1())}"

    def __setattr__(self, name: str, value: Any) -> None:
        with self.init_lock:
            if self.initalized:
                raise RuntimeError(
                    "You can not modify the system after the system has been initialized"
                )
            return super().__setattr__(name, value)

    def _print_init_message(self) -> None:
        print("*********************************************")
        print("*      Function Recording is enabled        *")
        print("*********************************************")
        print(f"** The save path is: {self.save_path}")

    def record(
        self,
        f: Callable,
        sample_size: int = 32,
    ):
        """Returns a list of :class:`bluepy.blte.Service` objects representing
        the services offered by the device. This will perform Bluetooth service
        discovery if this has not already been done; otherwise it will return a
        cached list of services immediately..

        :param uuids: A list of string service UUIDs to be discovered,
            defaults to None
        :type uuids: list, optional
        :return: A list of the discovered :class:`bluepy.blte.Service` objects,
            which match the provided ``uuids``
        :rtype: Callable[..., Any]
        """
        with self.init_lock:
            if not self.initalized:
                self.initalized = True
                if self.enabled:
                    self._print_init_message()
            if not self.enabled:
                return
        return _FunctionRecorder(
            f,
            sample_size=sample_size,
            save_path=self.save_path,
        )._f


DEFAULT_RECORDING_SYSTEM = _FunctionRecordingSystem()
record = DEFAULT_RECORDING_SYSTEM.record
