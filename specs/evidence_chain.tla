---- MODULE evidence_chain ----
EXTENDS Integers, Sequences
VARIABLES chain, lastHash
QuantumHash(x) == "SHAKE_" \o x
Init == chain = <<>> /\ lastHash = "0"*128
AddBlock(ev) == LET prev == IF chain=<<>> THEN "0"*128 ELSE lastHash IN chain' = Append(chain, [evidence |-> ev, prev |-> prev, chained |-> QuantumHash(prev \o ev)]) /\ lastHash' = QuantumHash(prev \o ev)
Inv_Crypto == \A i \in 1..Len(chain): chain[i].chained = QuantumHash(chain[i].prev \o chain[i].evidence)
Inv_Linkage == \A i \in 2..Len(chain): chain[i].prev = chain[i-1].chained
Next == \E ev \in STRING: AddBlock(ev)
Spec == Init /\ [][Next]_<<chain,lastHash>>
====