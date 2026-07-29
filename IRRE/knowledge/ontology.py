Entity("القاهرة", type="City", located_in="مصر")
Entity("Evidence", type="KnowledgeEntity", proves="Claim")
Relation("located_in", transitive=True) # لو أ في ب، و ب في ج → أ في ج
