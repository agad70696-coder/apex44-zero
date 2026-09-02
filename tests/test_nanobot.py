from IRRE.robotics.nanobot_evidence import NanobotEvidence


def test_nano_safe() -> None:
    swarm = NanobotEvidence("SWARM-01", "TUMOR-LUNG-01", "doxorubicin")
    swarm.add_movement(0.5, 0.5, 0.5, "cancer")
    swarm.add_movement(1.0, 1.0, 1.0, "cancer")
    assert swarm.is_mission_safe()


def test_attacking_healthy() -> None:
    swarm = NanobotEvidence("SWARM-02", "TUMOR-01", "chemo")
    swarm.add_movement(10, 10, 10, "healthy")  # راح لخلية سليمة بالكيماوي!
    assert not swarm.is_mission_safe()
