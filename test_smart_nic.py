import unittest
from simulator.smart_nic_simulator import SmartNICDevice
from backend.app.models import NodeStatus

class TestSmartNIC(unittest.TestCase):
    def test_smart_nic_device_initialization(self):
        nic = SmartNICDevice("nic-01", "10.0.1.1", "00:15:5d:01:02:03")
        self.assertEqual(nic.node_id, "nic-01")
        self.assertEqual(nic.status, NodeStatus.TRUSTED)
        self.assertTrue(nic.pcr_valid)
        self.assertEqual(nic.trust_score, 98.0)

    def test_smart_nic_telemetry_step(self):
        nic = SmartNICDevice("nic-01", "10.0.1.1", "00:15:5d:01:02:03")
        telem = nic.step_telemetry()
        self.assertEqual(telem.node_id, "nic-01")
        self.assertGreater(telem.rx_packets_sec, 0)
        self.assertTrue(telem.attestation.pcr_quote_valid)

    def test_smart_nic_firmware_tamper_and_remediate(self):
        nic = SmartNICDevice("nic-01", "10.0.1.1", "00:15:5d:01:02:03")
        nic.trigger_firmware_tamper()
        self.assertEqual(nic.status, NodeStatus.COMPROMISED)
        self.assertFalse(nic.pcr_valid)
        self.assertLess(nic.trust_score, 30.0)

        telem = nic.step_telemetry()
        self.assertGreater(telem.packet_tamper_events, 0)
        self.assertFalse(telem.attestation.pcr_quote_valid)

        nic.remediate()
        self.assertEqual(nic.status, NodeStatus.TRUSTED)
        self.assertTrue(nic.pcr_valid)
        self.assertEqual(nic.trust_score, 98.0)

if __name__ == '__main__':
    unittest.main()
