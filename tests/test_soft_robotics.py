from IRRE.robotics.soft_robotics_evidence import SoftRobotEvidence


def test_soft_safe() -> None:
    bot = SoftRobotEvidence("OCTO-01", "silicone")
    bot.add_grip(5.0, "heart")
    assert bot.is_grip_safe()


def test_crushing() -> None:
    bot = SoftRobotEvidence("OCTO-02", "hydrogel")
    bot.add_grip(40.0, "heart")  # ضغط يقطع القلب
    assert not bot.is_grip_safe()
