# RM-PERIPH-001

- **ID:** `RM-PERIPH-001`
- **Title:** Physical label printer integration for Niimbot thermal printers
- **Category:** `PERIPH`
- **Type:** `Feature`
- **Status:** `Planned`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `TBD`
- **Target horizon:** `later`
- **LOE:** `S`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description

Integrate Niimbot thermal label printer support (D11, B21, B1 models) for automated physical labeling, inventory marking, and cable management via Python library bindings and platform callable service.

## Why it matters

Platform lacks ability to generate and print physical labels for:
- inventory and asset management,
- cable and equipment identification,
- shipping and logistics labeling,
- organization and organization workflows.

Current workflows require manual label creation and external printer drivers, limiting automation potential.

## Reuse-first implementation approach

This item follows explicit reuse-first posture per `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`.

**Primary choice: niimprint (Python library)**
- Reason: Pure Python, cross-platform (Linux/Windows/macOS), Bluetooth and USB support, active community, simple API
- Mode: Adopt as full product
- Repository: https://github.com/AndBondStyle/niimprint
- Supported models: D11 (popular), B21 (budget), B1 (compact)
- Interface: Bluetooth (preferred) or USB
- Command structure: Connect → Queue print job → Dispatch → Verify

**Not to rebuild:**
- thermal printer driver,
- Bluetooth communication protocol,
- label format rendering,
- device discovery.

## Key requirements

### Hardware support
- Niimbot D11 thermal label printer (primary)
- Niimbot B21 thermal label printer (secondary)
- Niimbot B1 thermal label printer (tertiary)
- Bluetooth connectivity (preferred)
- USB connectivity (fallback)
- Device discovery and connection management
- Battery status and health monitoring

### Printer management requirements
- Device discovery and pairing (Bluetooth)
- Connection state tracking
- Printer health monitoring (battery, temperature, error states)
- Multiple printer support (home, office, mobile)
- Printer configuration (darkness, speed, density settings)
- Job queue and status tracking

### Label generation and printing requirements
- Support standard label sizes (25mm, 30mm, 50mm widths)
- QR code generation and printing
- Barcode generation (Code128, QR, EAN)
- Text rendering with font selection
- Image printing (logos, graphics)
- Label templates for common use cases (inventory, shipping, cable)
- Batch label printing (100+ labels)
- Print job preview before sending to device

### Integration point requirements
- Expose printer service via platform APIs
- REST/gRPC interface for print jobs
- Inventory system integration (RM-OPS-*)
- Automation triggers for label printing (cable labeling workflow)
- Print history and audit logging
- Status dashboard for printer health
- Alert notifications (low battery, errors)

### Software interface requirements
- Python service wrapper around niimprint library
- Async job queueing with persistence
- Label template engine (HTML/CSS or custom)
- API endpoints:
  - POST /print/label — Submit print job
  - GET /printer/status — Device status
  - GET /print/job/{id} — Job status
  - DELETE /print/job/{id} — Cancel job
- CLI tool for manual printing (for testing)

### Security and reliability requirements
- Bluetooth pairing secured (PIN if required)
- Print job history and audit trail
- Rate limiting to prevent printer overwhelm
- Error handling and graceful degradation
- Retry logic for failed prints
- Offline queue (save jobs if printer unavailable)
- Timeout management (long-running print jobs)

## Affected systems

- Physical asset and inventory management
- Cable and equipment labeling
- Shipping and logistics workflows
- Organization and storage systems
- Automation and orchestration layer

## Expected file families

- `framework/printer_service.py` — Label printer interface and job management
  - `niimbot_adapter.py` — niimprint library wrapper
  - `label_generator.py` — Label template and rendering
  - `printer_queue.py` — Job queueing and scheduling
- `config/printer/` — Printer configurations
  - `devices.yaml` — Printer device definitions
  - `templates.yaml` — Label template definitions
- `docker/docker-compose-printer.yml` — Printer service deployment (if containerized)
- `docs/runbooks/PRINTER_INTEGRATION.md` — Setup and usage guide
- `docs/runbooks/LABEL_TEMPLATES.md` — Creating and customizing label templates
- `tools/label_printer_cli.py` — CLI tool for manual printing
- `tests/test_printer_integration.py` — Integration tests

## Dependencies

- Python 3.11+
- niimprint library (PyPI or GitHub)
- Bluetooth stack (BlueZ on Linux, native on Windows/macOS)
- Platform job queueing system (RM-OPS-*)
- Inventory/asset management system (RM-OPS-*)

## External dependencies

### niimprint
- **Official repo:** https://github.com/AndBondStyle/niimprint
- **License:** MIT
- **Language:** Python 3.6+
- **Supported devices:** Niimbot D11, B21, B1
- **Interfaces:** Bluetooth (BLE/Classic), USB
- **Installation:** `pip install niimprint`
- **API:** Simple (connect, print, disconnect)
- **Maintenance:** Active community, regular updates
- **Adoption note:** `adopt-now` as primary printer library

### Bluetooth libraries
- **BlueZ** (Linux): Native Bluetooth stack
- **pybluez** (optional): Higher-level Python wrapper
- **Adoption note:** Platform-native Bluetooth should be used (BlueZ on Linux)

### Label generation
- **Pillow (PIL):** Image generation and manipulation
- **Reportlab:** PDF generation for label templates
- **QRCode:** QR code generation
- **Adoption note:** `adopt-selective` based on label complexity needs

## First milestone

Printer integration with:
1. niimprint library integrated and tested
2. Single Niimbot D11 discovered and connected
3. Basic text label printing working
4. QR code label generation and printing
5. Print job API endpoint (POST /print/label)
6. Job status tracking (GET /print/job/{id})
7. Error handling and retry logic
8. Printer status dashboard

## Autonomous execution guidance

### Pre-implementation
1. Acquire Niimbot printer (D11 recommended for first iteration)
2. Verify Bluetooth or USB connectivity to development machine
3. Test niimprint library locally with printer
4. Identify first use case (cable labeling, inventory, shipping)
5. Decide on label template approach (HTML/CSS or custom)

### Implementation sequence
1. **Library integration:**
   - Install niimprint: `pip install niimprint`
   - Create device discovery script (scan for Niimbot devices)
   - Implement basic connection and status check
   - Test printing simple text labels manually

2. **Printer service framework:**
   - Create `framework/printer_service.py`
   - Implement `NiimbotAdapter` wrapping niimprint
   - Add device management (discovery, pairing, reconnection)
   - Implement job queueing (SQLite or Redis)
   - Track job lifecycle (submitted, queued, printing, complete, failed)

3. **Label generation:**
   - Create `framework/label_generator.py`
   - Support template rendering (HTML/CSS or PIL)
   - Generate QR codes for labels
   - Generate barcodes if needed
   - Implement label previews

4. **API endpoints:**
   - POST /print/label — Submit label print job
   - GET /printer/status — Printer health and connectivity
   - GET /print/job/{id} — Check job status
   - DELETE /print/job/{id} — Cancel queued job
   - GET /print/templates — List available templates

5. **Configuration:**
   - Create `config/printer/devices.yaml` with printer definitions
   - Create `config/printer/templates.yaml` with label templates
   - Support multiple printers (by name and device address)
   - Configure print settings (darkness, speed, density)

6. **CLI tool:**
   - Create `tools/label_printer_cli.py`
   - Support commands: list-printers, print-text, print-qr, print-template
   - Test manual printing end-to-end
   - Validate label output quality

7. **Documentation:**
   - Create `docs/runbooks/PRINTER_INTEGRATION.md`
   - Document device pairing process (Bluetooth)
   - Document label template creation
   - Document troubleshooting (connection issues, print quality)

### Completion contract
- niimprint library integrated and tested
- Printer discovered, paired, and connected
- Text label printing working
- QR code label generation and printing functional
- API endpoints working for print jobs
- Job status tracking operational
- CLI tool for manual testing functional
- Multiple label templates defined
- Documentation complete

## Status transition

- Expected next status: `In Progress`
- Transition condition: Niimbot printer acquired, connectivity verified, niimprint library working
- Validation/closeout condition: Printer printing labels successfully, API endpoints live, job queue working, documentation complete

## Notes

Niimbot integration enables:
- Automated cable and equipment labeling
- Inventory and asset tracking with physical labels
- Shipping and logistics label generation
- Organization workflows (storage, logistics, identification)

Hardware considerations:
- D11: Popular model, good balance of price/performance
- B21: Budget option, smaller labels (25mm)
- B1: Compact and portable
- Bluetooth connectivity strongly preferred over USB (no drivers)

Software approach:
- Pure Python library (niimprint) avoids system dependencies
- Async job queueing prevents blocking on print operations
- Multiple printer support for scaling (office, home, mobile)
- Fallback queuing if printer offline

Risk mitigation:
- Device discovery may need retries (Bluetooth timeout)
- Print job failures → retry with backoff
- Printer offline → queue jobs until reconnected
- Label templates → provide sensible defaults to prevent manual work
