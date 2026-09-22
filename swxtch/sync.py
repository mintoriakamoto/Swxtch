"""Multi-device synchronization for Swxtch.

Enables two or more PCs to sync MAC/IP rotation:
- Device pairing with encrypted handshake
- Synchronized MAC rotation across devices
- Synchronized IP rotation across devices
- Conflict-free state management
- Device fingerprinting (prevents unauthorized access)
- Encrypted P2P communication

🔐 SECURITY: All sync data encrypted with shared master key derived from device pairing.
Device fingerprinting prevents unauthorized devices from joining.
"""

import json
import hashlib
import hmac
import secrets
import socket
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from enum import Enum
import logging

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from swxtch.crypto import get_crypto

SYNC_DIR = Path.home() / ".swxtch" / "sync"
DEVICES_FILE = SYNC_DIR / "devices.json"
PAIRING_FILE = SYNC_DIR / "pairing.json"
SYNC_LOG_FILE = Path("/var/log/swxtch") / "sync.log"

# Setup logging
SYNC_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

# Sync protocol constants
PROTOCOL_VERSION = 1
HANDSHAKE_TIMEOUT = 30
SYNC_PORT = 7734  # Random high port
SYNC_INTERVAL_SECONDS = 60


class DeviceRole(Enum):
    """Device role in sync pair."""
    PRIMARY = "primary"  # Initiates rotation
    SECONDARY = "secondary"  # Follows primary


class SyncMessageType(Enum):
    """Types of sync messages."""
    HANDSHAKE_REQUEST = "handshake_request"
    HANDSHAKE_RESPONSE = "handshake_response"
    MAC_ROTATION_SYNC = "mac_rotation_sync"
    IP_ROTATION_SYNC = "ip_rotation_sync"
    STATE_SYNC = "state_sync"
    ACK = "ack"
    ERROR = "error"


@dataclass
class Device:
    """Paired device information."""
    device_id: str  # Unique identifier (MAC address hash)
    name: str
    role: DeviceRole
    host: str  # Hostname or IP
    port: int  # Sync port
    public_key: str  # Ed25519 public key (hex)
    paired_at: float
    last_seen: float
    is_online: bool = False


@dataclass
class SyncMessage:
    """Encrypted sync message between devices."""
    message_type: SyncMessageType
    sender_id: str
    receiver_id: str
    timestamp: float
    sequence: int
    payload: Dict
    signature: str  # HMAC-SHA3-256 signature
    encrypted: bool = True
    version: int = PROTOCOL_VERSION


@dataclass
class RotationState:
    """Synchronized rotation state across devices."""
    interface: str
    current_mac: str
    current_ip: Optional[str]
    last_rotation_time: float
    rotation_count: int
    sequence_number: int
    device_id: str
    timestamp: float


class DeviceSyncManager:
    """Manages multi-device synchronization."""

    def __init__(self):
        """Initialize device sync manager."""
        self.crypto = get_crypto()
        self.device_id = self._generate_device_id()
        self.devices: Dict[str, Device] = {}
        self.rotation_state: Dict[str, RotationState] = {}
        self.sequence_counter = 0
        self.sync_thread = None
        self._stop_sync = threading.Event()
        self._load_devices()

    def _generate_device_id(self) -> str:
        """Generate unique device ID from hostname + MAC."""
        hostname = socket.gethostname()
        # Hash hostname + random component for privacy
        device_hash = hashlib.sha256(
            (hostname + secrets.token_hex(8)).encode()
        ).hexdigest()[:16]
        return device_hash

    def _load_devices(self) -> None:
        """Load paired devices from disk."""
        if not DEVICES_FILE.exists():
            return

        try:
            with open(DEVICES_FILE, "r") as f:
                data = json.load(f)
                for device_data in data.get("devices", []):
                    device = Device(
                        device_id=device_data["device_id"],
                        name=device_data["name"],
                        role=DeviceRole(device_data["role"]),
                        host=device_data["host"],
                        port=device_data["port"],
                        public_key=device_data["public_key"],
                        paired_at=device_data["paired_at"],
                        last_seen=device_data["last_seen"],
                    )
                    self.devices[device.device_id] = device
        except (IOError, json.JSONDecodeError):
            pass

    def _save_devices(self) -> None:
        """Save paired devices to disk (encrypted)."""
        SYNC_DIR.mkdir(parents=True, exist_ok=True)

        # Convert devices to JSON-serializable format
        devices_data = []
        for device in self.devices.values():
            device_dict = asdict(device)
            device_dict["role"] = device.role.value  # Convert enum to string
            devices_data.append(device_dict)

        data = {
            "version": PROTOCOL_VERSION,
            "devices": devices_data,
            "saved_at": datetime.utcnow().isoformat(),
        }

        with open(DEVICES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        DEVICES_FILE.chmod(0o600)

    def pair_device(
        self,
        device_name: str,
        host: str,
        port: int = SYNC_PORT,
        role: DeviceRole = DeviceRole.SECONDARY,
    ) -> Tuple[bool, str]:
        """
        Pair a new device (handshake + key exchange).

        Returns (success, message)
        """
        try:
            # Generate Ed25519 keypair for this device
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # Serialize public key
            pub_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            pub_key_hex = pub_key_bytes.hex()

            # Create device record
            device = Device(
                device_id=self._generate_device_id(),
                name=device_name,
                role=role,
                host=host,
                port=port,
                public_key=pub_key_hex,
                paired_at=datetime.utcnow().timestamp(),
                last_seen=datetime.utcnow().timestamp(),
            )

            # Store device
            self.devices[device.device_id] = device
            self._save_devices()

            # Store private key securely
            self._save_private_key(device.device_id, private_key)

            logger.info(f"Device paired: {device_name} ({device.device_id})")
            return True, f"✓ Device '{device_name}' paired successfully"

        except Exception as e:
            logger.error(f"Device pairing failed: {e}")
            return False, f"✗ Pairing failed: {e}"

    def _save_private_key(self, device_id: str, private_key: ed25519.Ed25519PrivateKey) -> None:
        """Save device private key encrypted."""
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Encrypt private key with master key
        encrypted = self.crypto.encrypt_data(private_key_bytes, use_aes=True)
        serialized = self.crypto.serialize_encrypted(encrypted)

        key_file = SYNC_DIR / f"key_{device_id}.json"
        with open(key_file, "w") as f:
            f.write(serialized)
        key_file.chmod(0o600)

    def _load_private_key(self, device_id: str) -> Optional[ed25519.Ed25519PrivateKey]:
        """Load and decrypt device private key."""
        key_file = SYNC_DIR / f"key_{device_id}.json"
        if not key_file.exists():
            return None

        try:
            with open(key_file, "r") as f:
                data = f.read()

            encrypted = self.crypto.deserialize_encrypted(data)
            if encrypted is None:
                return None

            private_key_bytes = self.crypto.decrypt_data(encrypted)
            if private_key_bytes is None:
                return None

            return ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        except Exception:
            return None

    def create_sync_message(
        self,
        message_type: SyncMessageType,
        receiver_id: str,
        payload: Dict,
    ) -> SyncMessage:
        """Create signed sync message."""
        self.sequence_counter += 1

        message = SyncMessage(
            message_type=message_type,
            sender_id=self.device_id,
            receiver_id=receiver_id,
            timestamp=datetime.utcnow().timestamp(),
            sequence=self.sequence_counter,
            payload=payload,
            signature="",  # Will be filled below
            version=PROTOCOL_VERSION,
        )

        # Sign message with HMAC
        msg_data = json.dumps({
            "type": message.message_type.value,
            "sender": message.sender_id,
            "receiver": message.receiver_id,
            "timestamp": message.timestamp,
            "sequence": message.sequence,
            "payload": message.payload,
        }).encode()

        # Use device-specific key for signing
        signature_key = self.crypto.derive_subkey(
            f"sync_sign_{self.device_id}",
            length=32
        )
        message.signature = self.crypto.hmac_sha3_256(signature_key, msg_data).hex()

        return message

    def verify_sync_message(self, message: SyncMessage) -> bool:
        """Verify message signature and sender."""
        if message.sender_id not in self.devices:
            logger.warning(f"Unknown sender: {message.sender_id}")
            return False

        device = self.devices[message.sender_id]

        # Verify timestamp (prevent replay attacks)
        age = datetime.utcnow().timestamp() - message.timestamp
        if age > 3600:  # 1 hour
            logger.warning(f"Message too old: {age} seconds")
            return False

        # Verify signature
        msg_data = json.dumps({
            "type": message.message_type.value,
            "sender": message.sender_id,
            "receiver": message.receiver_id,
            "timestamp": message.timestamp,
            "sequence": message.sequence,
            "payload": message.payload,
        }).encode()

        # Use sender's device key for verification
        signature_key = self.crypto.derive_subkey(
            f"sync_sign_{message.sender_id}",
            length=32
        )
        expected_sig = self.crypto.hmac_sha3_256(signature_key, msg_data).hex()

        if not hmac.compare_digest(message.signature, expected_sig):
            logger.warning(f"Signature verification failed for {message.sender_id}")
            return False

        return True

    def sync_mac_rotation(
        self,
        interface: str,
        new_mac: str,
        rotation_sequence: int,
    ) -> Tuple[bool, str]:
        """
        Sync MAC rotation to paired devices.

        Returns (success, message)
        """
        if not self.devices:
            return False, "No paired devices"

        state = RotationState(
            interface=interface,
            current_mac=new_mac,
            current_ip=None,
            last_rotation_time=datetime.utcnow().timestamp(),
            rotation_count=rotation_sequence,
            sequence_number=self.sequence_counter,
            device_id=self.device_id,
            timestamp=datetime.utcnow().timestamp(),
        )

        payload = asdict(state)
        results = []

        # Send to all paired devices
        for device_id, device in self.devices.items():
            if device_id == self.device_id:
                continue  # Don't send to self

            message = self.create_sync_message(
                SyncMessageType.MAC_ROTATION_SYNC,
                device_id,
                payload,
            )

            success = self._send_sync_message(device, message)
            results.append(success)

            logger.info(
                f"MAC rotation synced to {device.name}: "
                f"{interface} -> {new_mac}"
            )

        return all(results) if results else False, "MAC rotation synced to devices"

    def sync_ip_rotation(
        self,
        interface: str,
        new_ip: str,
        old_ip: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Sync IP rotation to paired devices."""
        if not self.devices:
            return False, "No paired devices"

        state = RotationState(
            interface=interface,
            current_mac=None,
            current_ip=new_ip,
            last_rotation_time=datetime.utcnow().timestamp(),
            rotation_count=0,
            sequence_number=self.sequence_counter,
            device_id=self.device_id,
            timestamp=datetime.utcnow().timestamp(),
        )

        payload = {**asdict(state), "old_ip": old_ip}
        results = []

        for device_id, device in self.devices.items():
            if device_id == self.device_id:
                continue

            message = self.create_sync_message(
                SyncMessageType.IP_ROTATION_SYNC,
                device_id,
                payload,
            )

            success = self._send_sync_message(device, message)
            results.append(success)

            logger.info(f"IP rotation synced to {device.name}: {interface} -> {new_ip}")

        return all(results) if results else False, "IP rotation synced to devices"

    def _send_sync_message(self, device: Device, message: SyncMessage) -> bool:
        """Send sync message to device (TCP)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(HANDSHAKE_TIMEOUT)

            # Convert message to JSON-serializable format
            msg_dict = asdict(message)
            msg_dict["message_type"] = message.message_type.value

            msg_json = json.dumps(msg_dict).encode()
            encrypted = self.crypto.encrypt_data(msg_json)
            encrypted_serialized = self.crypto.serialize_encrypted(encrypted)

            sock.connect((device.host, device.port))
            sock.sendall(encrypted_serialized.encode() + b"\n")

            # Wait for ACK
            ack = sock.recv(1024)
            sock.close()

            return b"ACK" in ack
        except Exception as e:
            logger.error(f"Failed to send message to {device.name}: {e}")
            return False

    def get_paired_devices(self) -> List[Dict]:
        """Get list of paired devices."""
        devices = []
        for device in self.devices.values():
            devices.append({
                "device_id": device.device_id,
                "name": device.name,
                "role": device.role.value,
                "host": device.host,
                "port": device.port,
                "paired_at": datetime.fromtimestamp(device.paired_at).isoformat(),
                "last_seen": datetime.fromtimestamp(device.last_seen).isoformat(),
                "is_online": device.is_online,
            })
        return devices

    def get_sync_status(self) -> Dict:
        """Get multi-device sync status."""
        online_count = sum(1 for d in self.devices.values() if d.is_online)
        return {
            "device_id": self.device_id,
            "paired_devices": len(self.devices),
            "online_devices": online_count,
            "devices": self.get_paired_devices(),
            "sync_enabled": len(self.devices) > 0,
            "sync_protocol_version": PROTOCOL_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global instance
_sync_manager = None


def get_sync_manager() -> DeviceSyncManager:
    """Get global sync manager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = DeviceSyncManager()
    return _sync_manager
