from egfr_discovery.adapters.outbound.persistence.filesystem_pipeline_documentation import (
    FilesystemPipelineDocumentationOutput,
)
from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentation,
    GeneratePipelineDocumentationCommand,
    GeneratePipelineDocumentationResult,
)

PIPELINE_DOCUMENTATION_REGISTRY = PipelineDocumentationRegistry(
    pipelines=(
        PipelineDocumentation(
            pipeline_id="egfr_screening",
            title="EGFR Small-Molecule Screening Pipeline",
            summary=(
                "This pipeline prioritizes small molecules that may inhibit EGFR "
                "for research follow-up."
            ),
            sections=(
                PipelineDocumentationSection(
                    key="plain_language_summary",
                    heading="Plain-Language Summary",
                    body=(
                        "EGFR is a protein whose altered forms can help some cancers "
                        "grow. This pipeline learns patterns from previous laboratory "
                        "measurements of compounds tested against EGFR. It estimates "
                        "which compounds in a new list may be more active, removes "
                        "candidates with unfavorable basic properties, avoids returning "
                        "many nearly identical compounds, and ranks a shortlist for "
                        "laboratory follow-up. This is useful because laboratory testing "
                        "is costly and slow, so computational prioritization helps "
                        "researchers decide what to test first. The shortlist is a set "
                        "of research hypotheses, not proof that any compound works."
                    ),
                ),
                PipelineDocumentationSection(
                    key="inputs",
                    heading="Input Summary",
                    body=(
                        "Model development starts from ChEMBL EGFR IC50 measurements. "
                        "IC50 is the concentration associated with 50% inhibition in "
                        "an assay. The default pipeline retains exact, positive IC50 "
                        "values reported in nM, validates structures, records rejected "
                        "data with reasons, preserves source values and provenance, "
                        "and separates training and validation records by compound. "
                        "Screening input is a caller-provided CSV with `compound_id` "
                        "and `smiles` columns. SMILES is a text notation for molecular "
                        "structure. An EGFR target label alone does not establish "
                        "activity against a particular mutant form."
                    ),
                ),
                PipelineDocumentationSection(
                    key="prediction_and_features",
                    heading="Prediction Target and Features",
                    body=(
                        "The model predicts continuous pIC50, the negative base-10 "
                        "logarithm of IC50 in molar units. A larger value represents "
                        "a lower predicted concentration for 50% inhibition. Features "
                        "are character-level TF-IDF n-grams of lengths one through "
                        "three derived from each SMILES string: weighted patterns of "
                        "one, two, or three characters. They do not represent measured "
                        "binding, a three-dimensional binding pose, safety, or clinical "
                        "efficacy."
                    ),
                ),
                PipelineDocumentationSection(
                    key="models_and_rationale",
                    heading="Models and Rationale",
                    body=(
                        "The activity model uses a `RandomForestRegressor`, "
                        "deterministic for the same data, settings, software, and "
                        "random seed. A nonlinear tree ensemble can learn interactions "
                        "in the sparse SMILES-derived representation without assuming "
                        "a linear response. The population standard deviation across "
                        "individual tree predictions is reported as model dispersion; "
                        "it is not calibrated experimental uncertainty. Held-out "
                        "validation must pass the configured acceptance criteria "
                        "before the caller's library is screened."
                    ),
                ),
                PipelineDocumentationSection(
                    key="drug_discovery_use",
                    heading="How Predictions Are Used in Drug Discovery",
                    body=(
                        "Predicted pIC50 is combined with deterministic molecular "
                        "descriptors and explicit property filters. Morgan-fingerprint "
                        "similarity then supports diversity selection so the shortlist "
                        "does not contain only close structural analogues. A ranking "
                        "step combines predicted potency, properties, and model "
                        "dispersion to prioritize compounds for expert review and "
                        "experimental testing."
                    ),
                ),
                PipelineDocumentationSection(
                    key="drug_discovery_value",
                    heading="Why This Information Is Useful",
                    body=(
                        "Computational prioritization can reduce a large library to a "
                        "smaller and more chemically varied set of hypotheses, making "
                        "experimental resources easier to focus. Predicted pIC50 and "
                        "model dispersion support relative comparison, but they "
                        "do not establish potency, selectivity, safety, developability, "
                        "or clinical utility and must not be used as a clinical "
                        "recommendation."
                    ),
                ),
            ),
        ),
    )
)


def build_pipeline_documentation_generator() -> GeneratePipelineDocumentation:
    return GeneratePipelineDocumentation(
        PIPELINE_DOCUMENTATION_REGISTRY,
        FilesystemPipelineDocumentationOutput(),
    )


def run_pipeline_documentation(
    command: GeneratePipelineDocumentationCommand,
) -> GeneratePipelineDocumentationResult:
    return build_pipeline_documentation_generator().execute(command)
