from IRRE.robotics.autonomous_evidence import AutonomousRobotEvidence

def test_auto_safe():
    bot = AutonomousRobotEvidence("ATLAS-01", "rescue")
    bot.add_decision("lift_rubble", 0.95, False)
    assert bot.is_mission_compliant() == True

def test_risky_decision():
    bot = AutonomousRobotEvidence("ATLAS-02", "surgery")
    bot.add_decision("cut_artery", 0.4, False)  # ثقة 40% ويقطع شريان لوحده!
    assert bot.is_mission_compliant() == False
