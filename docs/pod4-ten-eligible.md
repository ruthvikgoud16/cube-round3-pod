# Ten eligible sample units through all five agents

These ten are the dummy sample units that have a Receiving row, a Prep row, a Returns row, and a fee row. No sample unit has both Prep and Pack. Pack is called anyway because this uses `flow.pod4-tracers.json`. Pack returns UNCERTAIN: there is no pack row to replay. This is not a Claude run.

| Unit | Product | Workflow | Outcome | Receiving | Prep | Pack | Returns | Recovery |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNIT-0003 | Jigsaw Puzzle 500pc | BLOCKED | EXCEPTION | UNCERTAIN | FAIL | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0014 | LED Desk Lamp | BLOCKED | NEEDS_REVIEW | PASS | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0018 | Steel Water Bottle | BLOCKED | NEEDS_REVIEW | PASS | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0030 | Vitamin C Face Serum 30ml | BLOCKED | EXCEPTION | PASS | FAIL | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0036 | Jigsaw Puzzle 500pc | BLOCKED | EXCEPTION | FAIL | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0038 | Whey Protein | BLOCKED | NEEDS_REVIEW | PASS | UNCERTAIN | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0039 | Vitamin C Face Serum 30ml | BLOCKED | NEEDS_REVIEW | PASS | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0041 | Nylon Dog Leash | BLOCKED | NEEDS_REVIEW | PASS | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0048 | Soy Candle Trio | BLOCKED | NEEDS_REVIEW | PASS | PASS | UNCERTAIN | PASS | UNCERTAIN |
| UNIT-0050 | Jigsaw Puzzle 500pc | BLOCKED | EXCEPTION | FAIL | UNCERTAIN | UNCERTAIN | PASS | UNCERTAIN |

## Stage reasons

### UNIT-0003 Jigsaw Puzzle 500pc — BLOCKED / EXCEPTION
- receiving completed UNCERTAIN replayed receiving sample row
- prep completed FAIL replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN weight, lost, or warehouse line; mock does not recommend a claim

### UNIT-0014 LED Desk Lamp — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN sample charge has no photo that can support or contradict it

### UNIT-0018 Steel Water Bottle — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN sample charge has no photo that can support or contradict it

### UNIT-0030 Vitamin C Face Serum 30ml — BLOCKED / EXCEPTION
- receiving completed PASS replayed receiving sample row
- prep completed FAIL replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN weight, lost, or warehouse line; mock does not recommend a claim

### UNIT-0036 Jigsaw Puzzle 500pc — BLOCKED / EXCEPTION
- receiving completed FAIL replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN weight, lost, or warehouse line; mock does not recommend a claim

### UNIT-0038 Whey Protein — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed UNCERTAIN replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN sample charge has no photo that can support or contradict it

### UNIT-0039 Vitamin C Face Serum 30ml — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN weight, lost, or warehouse line; mock does not recommend a claim

### UNIT-0041 Nylon Dog Leash — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN sample charge has no photo that can support or contradict it

### UNIT-0048 Soy Candle Trio — BLOCKED / NEEDS_REVIEW
- receiving completed PASS replayed receiving sample row
- prep completed PASS replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN sample charge has no photo that can support or contradict it

### UNIT-0050 Jigsaw Puzzle 500pc — BLOCKED / EXCEPTION
- receiving completed FAIL replayed receiving sample row
- prep completed UNCERTAIN replayed prep sample row
- pack completed UNCERTAIN no sample row
- returns completed PASS replayed returns sample row
- recovery completed UNCERTAIN weight, lost, or warehouse line; mock does not recommend a claim

## Agent failure on UNIT-0014, the LED desk lamp

### Receiving is down, then resume
First pass, connection refused on both attempts:
```
{
  "status": "FAILED",
  "outcome": "INCOMPLETE",
  "reason": "stage did not complete: receiving",
  "halted": null,
  "stages": [
    "receiving error UNCERTAIN",
    "prep completed PASS",
    "pack completed UNCERTAIN",
    "returns completed PASS",
    "recovery completed UNCERTAIN"
  ]
}
```
Receiving attempts while down: 2.

Resume after Receiving answers:
```
{
  "status": "BLOCKED",
  "outcome": "NEEDS_REVIEW",
  "reason": "a person must decide: pack, recovery",
  "halted": null,
  "stages": [
    "receiving completed PASS",
    "prep completed PASS",
    "pack completed UNCERTAIN",
    "returns completed PASS",
    "recovery completed UNCERTAIN"
  ]
}
```

### Prep returns a bare 422
```
{
  "status": "FAILED",
  "outcome": "INCOMPLETE",
  "reason": "stage did not complete: prep",
  "halted": "stage prep did not judge (status=error); not continuing",
  "stages": [
    "receiving completed PASS",
    "prep error UNCERTAIN",
    "pack pending None",
    "returns pending None",
    "recovery pending None"
  ]
}
```

Receiving's judgment is kept. Prep is stored as an error, not a crash of the process. Pack, Returns, and Recovery are not called after that refusal.
