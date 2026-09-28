from egfr_discovery.application.use_cases.ingest_bioactivity_data import (
    IngestBioactivityCommand,
)
from egfr_discovery.bootstrap.ingest import run_ingestion


def main() -> None:

    result = run_ingestion(
        IngestBioactivityCommand(
            target_id="CHEMBL203",
            activity_type="IC50",
            dataset_version="v1",
        )
    )

    print()
    print("Ingestion complete")
    print("------------------")
    print(f"Downloaded: {result.downloaded_records}")
    print(f"Accepted:   {result.accepted_records}")
    print(f"Raw:        {result.raw_file}")
    print(f"Processed:  {result.processed_file}")
    print(f"Report:     {result.report_file}")


if __name__ == "__main__":
    main()
