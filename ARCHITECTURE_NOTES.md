Think of Hexagonal Architecture (also known as "Ports and Adapters") like a highly secure, sterile laboratory.

The scientists inside (your core business logic) do the most important work, but they aren't allowed to leave the room. They don't care how the mail gets delivered or where the filing cabinets are stored. They just have an "Inbox" for receiving instructions and an "Outbox" for requesting information.

In Python, this architecture keeps your core application completely isolated from the outside world (like web frameworks, databases, or external APIs).

---

## The Three Layers (Drug Discovery Example)

Let's apply this to a **Molecule Screening Service**, an application where a scientist inputs a chemical structure, and the system calculates its potential as a drug and saves the results.

### 1. The Core (The Center of the Hexagon)

This is your pure Python code. It contains the rules for validating a molecule and calculating its score. It contains **no dependencies** on FastAPI, SQL, or external web services. It only knows about "Molecule" objects and the rules of chemistry.

### 2. The Ports (The Edges of the Hexagon)

Ports are the "contracts" or interfaces (often written using Python's `abc.ABC` module) that define how data gets in and out of the Core.

* **Primary Port (Inbound):** The interface for talking *to* the Core. Example: A `MoleculeAnalyzer` interface that says, "If you give me a chemical string, I will return a score."
* **Secondary Port (Outbound):** The interface for the Core to talk to the *outside world*. Example: A `MoleculeRepository` interface that says, "I have a method to save a molecule, but I don't care how it gets saved."

### 3. The Adapters (The Outside World)

Adapters are the translators that connect the outside world to your Ports.

* **Primary Adapter (Driving):** The tool the scientist interacts with. In this case, a **FastAPI web endpoint**. It takes an HTTP request, unpacks the JSON, and feeds it into the Primary Port.
* **Secondary Adapter (Driven):** The tools that do the heavy lifting for the Core. In this case, a **PostgreSQL database connector** that implements the Secondary Port's "save" method by actually writing SQL.

---

## The Request Flow

Here is exactly what happens step-by-step when a scientist uses this pipeline to test a new molecule:

1. **Scientist Submits Data:**
A researcher sends an HTTP `POST` request to your application containing a chemical SMILES string (e.g., `CCO` for ethanol).


2. **Primary Adapter Translates (Inbound):**
The FastAPI web router (Primary Adapter) catches the HTTP request. It strips away all the web-specific headers and JSON formatting, turning the payload into a plain Python object.


3. **Primary Port Routes to Core:**
The adapter passes this Python object through the Inbound Port to your Core Domain.


4. **Core Executes Business Logic:**
Your pure Python rules take over. The Core validates the chemical structure and runs the screening algorithm to generate a viability score.


5. **Core Requests Data Storage:**
The Core decides the result needs to be saved. It calls the `save()` method on the Outbound Port. The Core doesn't know *where* it's saving—it just trusts the port.


6. **Secondary Adapter Saves the Data (Outbound):**
The PostgreSQL adapter, which is plugged into that Outbound Port, translates the `save()` command into an `INSERT INTO` SQL query and commits it to the database.


7. **Result Returns to Scientist:**
The database confirms the save, the Core returns the score back through the Inbound Port to the FastAPI adapter, which packages it back into an HTTP response and sends it to the scientist's screen.


The beauty of this flow is flexibility. If you want to switch from FastAPI to a CLI tool, or switch from PostgreSQL to a cloud database, you only rewrite the **Adapters**. The Core rules of drug discovery remain completely untouched.