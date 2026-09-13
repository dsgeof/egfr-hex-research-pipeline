# Research Pipeline

### Important: Dependency Direction: 
Adapters → Application → Domain
NOT: Domain → Adapters

1. Import core dependencies
2. Define directory structure
3. Create Agents.md with instructions

5. Build the first domain objects : /src/egfr_discovery/domain/**compound.py**

7. Define the Machine-Learning Port
**The application layer should not know whether you use scikit-learn, PyTorch or another library.**
Create src/egfr_discovery/application/**ports**/activity_model.py
This is a **port**. Later, an sklearn implementation will be the adapter:
```python
class ActivityModel(Protocol):
    def train(self, compounds: Sequence[Compound], labels: Sequence[int]) -> None:
        """Train the activity model."""
    def predict(self, compounds: Sequence[Compound]) -> list[ActivityPrediction]:
        """Predict activity for compounds."""

```


Sklearn adapter
    imports Application/Domain concepts

Application/domain
    DOES NOT import sklearn adapter

9. Create the Training Use Case: src/egfr_discovery/**application/use_cases/train_activity_model.py**

10. Wire It Together: src/egfr_discovery/bootstrap/container.py