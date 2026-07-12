

## Overview

This repository contains the implementation, XML schema definitions, protocol adapters, and experimental artifacts used in the paper:

**"NDIEM: A Novel Drone Information Exchange Model for Semantic Interoperability of Heterogeneous UAV Systems"**

The proposed NDIEM framework provides a canonical information exchange model that enables semantic interoperability among heterogeneous UAV platforms operating with different communication protocols. The framework normalizes telemetry, command and control, mission, sensor, and identification data into a unified XML-based representation.

Supported UAV communication protocols include:

* MAVLink (ArduPilot/PX4-based UAVs)
* CRTP (Crazyflie UAVs)
* Tello EDU SDK (UDP-based communication)

The repository contains the XML schema, message translation modules, validation components, and evaluation scripts used in the experimental study.

---

## Repository Contents

```text
├── schema/
│   └── drone.xsd
├── adapters/
│   ├── mavlink_adapter.py
│   ├── crazyflie_adapter.py
│   └── tello_adapter.py
├── validator/
│   └── xml_validator.py
├── examples/
│   └── sample_xml_messages/
├── experiments/
│   └── evaluation_scripts/
└── README.md
```

---

## Software Environment

The prototype implementation and experimental evaluation reported in the paper were conducted using the following software environment.

| Component           | Version                             |
| ------------------- | ----------------------------------- |
| Operating System    | Microsoft Windows 11 (64-bit)       |
| Python              | 3.13.1                              |
| Eclipse Papyrus     | 2025-06 (Version 7.1.0)             |
| XML Schema Standard | W3C XML Schema Definition (XSD 1.0) |

---

## Python Libraries

The prototype implementation relies on the following libraries.

| Library               | Version                 | Purpose                                        |
| --------------------- | ----------------------- | ---------------------------------------------- |
| pymavlink             | 2.4.47                  | MAVLink communication and telemetry parsing    |
| lxml                  | 6.0.0                   | XML generation, parsing, and schema validation |
| socket                | Python Standard Library | UDP communication with Tello EDU               |
| xml.etree.ElementTree | Python Standard Library | XML document processing                        |
| threading             | Python Standard Library | Concurrent message processing                  |
| time                  | Python Standard Library | Latency measurement                            |
| logging               | Python Standard Library | Runtime logging and debugging                  |

### Installation

```bash
pip install pymavlink==2.4.47
pip install lxml==6.0.0
```

---

## Modeling Environment

The conceptual information model, UML class diagrams, and schema design were developed using:

**Eclipse Papyrus 2025-06 (Version 7.1.0)**

Papyrus was used to model the UAV information structure prior to XML Schema implementation and message transformation development.

---

## Experimental Platforms

The framework was evaluated using heterogeneous UAV communication environments including:

### MAVLink-Based UAV

* ArduPilot/PX4 compatible platforms
* MAVLink telemetry and command messages

### Crazyflie UAV

* Crazyflie 2.x platform
* CRTP communication protocol

### Tello EDU

* DJI Tello EDU
* UDP-based SDK communication

These platforms were selected to represent heterogeneous UAV ecosystems with different communication protocols and message structures.

---

## Experimental Procedure

The experimental workflow consists of the following steps:

1. Capture native UAV telemetry data.
2. Extract protocol-specific information fields.
3. Transform native messages into the NDIEM canonical XML structure.
4. Validate generated XML messages using the provided XML Schema.
5. Exchange normalized messages through the NDIEM middleware layer.
6. Measure interoperability, validation success, and transformation latency.

---

## Reproducibility

To reproduce the experiments reported in the paper:

1. Install Python 3.13.1.
2. Install the required libraries:

   * pymavlink 2.4.47
   * lxml 6.0.0
3. Clone this repository.
4. Connect the target UAV platform or use the provided sample datasets.
5. Execute the corresponding protocol adapter.
6. Generate canonical XML messages.
7. Validate XML messages using the provided schema.
8. Execute the evaluation scripts to reproduce latency and interoperability results.

---

## Repository Release

This repository corresponds to the implementation used in the published experimental evaluation.

**Release Version:** v1.0

Researchers are encouraged to cite this repository version when reproducing or extending the presented work.

---



## Availability

The exact software environment, implementation source code, XML schema definitions, and experimental artifacts used in the study are publicly available through this repository.

The prototype was implemented in Python 3.13.1 on Microsoft Windows 11, while the conceptual information model was designed using Eclipse Papyrus 2025-06 (Version 7.1.0).
