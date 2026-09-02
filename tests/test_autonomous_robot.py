from IRRE.robotics.autonomous_evidence import AutonomousRobotEvidence


def test_auto_safe() -> None:
    bot = AutonomousRobotEvidence("ATLAS-01", "rescue")
    bot.add_decision("lift_rubble", 0.95, False)
    assert bot.is_mission_compliant()


def test_risky_decision() -> None:
    bot = AutonomousRobotEvidence("ATLAS-02", "surgery")
    bot.add_decision("cut_artery", 0.4, False)  # ثقة 40% ويقطع شريان لوحده!
    assert not bot.is_mission_compliant()
