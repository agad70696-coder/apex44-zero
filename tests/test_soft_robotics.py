from IRRE.robotics.soft_robotics_evidence import SoftRobotEvidence

def test_soft_safe():
    bot = SoftRobotEvidence("OCTO-01", "silicone")
    bot.add_grip(5.0, "heart")
    assert bot.is_grip_safe() == True

def test_crushing():
    bot = SoftRobotEvidence("OCTO-02", "hydrogel")
    bot.add_grip(40.0, "heart")  # ضغط يقطع القلب
    assert bot.is_grip_safe() == False
