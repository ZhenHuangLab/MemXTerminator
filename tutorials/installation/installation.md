---
comments: true
---

# Installation

## Requirements

* NVIDIA GPU with CUDA drivers and libraries
* `cupy` library
* other dependencies (e.g. `mrcfile`)

!!! note
    Please note that the corresponding python libraries will be automatically installed during the installation process of this software.

## How to install

### Step 1: Clone repository

```bash

git clone https://github.com/ZhenHuangLab/MemXTerminator.git

```

### Step 2: Create a virtual environment

```bash

conda create -n mxt python=3.9

conda activate mxt

```

### Step 3: Install software and dependencies

```bash

cd MemXTerminator

pip install .

```

## How to update

Please get to the source-code dictionary downloaded from the repository, for example:

```bash

cd MemXTerminator

```

Then, run the following command:

```bash

git pull

pip install .

```
