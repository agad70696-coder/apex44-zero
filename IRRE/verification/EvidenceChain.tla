---------------- MODULE EvidenceChain ----------------
EXTENDS Naturals, Sequences, TLC

VARIABLES chain, nextId

GenesisHash == "APEX-GENESIS-V8-PQC-HASH"

TypeOK ==
  /\ chain \in Seq([id: Nat, prev: STRING, chained: STRING])

Init ==
  /\ chain = <<[id |-> 1, prev |-> "000", chained |-> GenesisHash]>>
  /\ nextId = 2

AddBlock(prevHash, newChained) ==
  /\ chain' = Append(chain, [id |-> nextId, prev |-> prevHash, chained |-> newChained])
  /\ nextId' = nextId + 1

Next ==
  \E p, c \in STRING: AddBlock(p, c)

Inv_NoTamper ==
  \A i \in 2..Len(chain): chain[i].prev = chain[i-1].chained

Inv_Genesis ==
  Len(chain) >= 1 /\ chain[1].chained = GenesisHash

Spec == Init /\ [][Next]_<<chain, nextId>>
THEOREM Spec => []Inv_NoTamper
