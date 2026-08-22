import re
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[1] / "DataForge" / "faxit-rewards.dataasset.yml"
EXPECTED_TASK_IDS = {
    *(f"Reward_Somersloop_{index}" for index in range(1, 6)),
    *(f"Reward_Mercer_{index}" for index in range(1, 6)),
}
AMOUNT_RANGE_PATTERN = re.compile(
    r"mAmountRange:\s+"
    r"LowerBound:\s+Type: Inclusive\s+Value: (\d+)\s+"
    r"UpperBound:\s+Type: Exclusive\s+Value: (\d+)"
)


def main() -> None:
    text = DATA_FILE.read_text(encoding="utf-8")
    task_blocks = {
        task_id: block
        for task_id, block in re.findall(
            r"^  - id: (Reward_(?:Somersloop|Mercer)_\d+)\n(.*?)(?=^  - id: |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
    }

    assert task_blocks.keys() == EXPECTED_TASK_IDS, (
        f"expected recovery tasks {sorted(EXPECTED_TASK_IDS)}, got {sorted(task_blocks)}"
    )

    for task_id, block in task_blocks.items():
        assert re.search(r"path: bIsEndless\s+value: true", block), f"{task_id} is not endless"
        assert re.search(r"path: mMaxPoolItems\s+value: 5", block), f"{task_id} does not select five pool items"

        ranges = AMOUNT_RANGE_PATTERN.findall(block)
        assert ranges, f"{task_id} has no pool amount ranges"
        invalid_ranges = [amount_range for amount_range in ranges if amount_range != ("50", "201")]
        assert not invalid_ranges, f"{task_id} has amount ranges outside inclusive 50-200: {invalid_ranges}"

    print(
        f"PASS: {len(task_blocks)} endless recovery tasks use five pool items "
        "with inclusive base amounts 50-200"
    )


if __name__ == "__main__":
    main()
