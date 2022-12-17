# audio-labeler

This is a simple tool built using PyQt5 to label audio. Nothing too fancy - but improves productivity quite a bit.

## Installation

Create virtual environment

```
python -m venv env
source env/bin/activate
```

Upgrade pip and install requirements:

```
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Usage
- Add a folder called 'audiofiles' in the working directory and move your audiofiles there
- Modify the `labels.json` file according to the logic `label:hex-color`. You can add more labels. The `failed` label is mandatory.
- Run the program with `python labeler.py`

1. Load the audiofiles by pressing `Import`
2. Select the correct label from the radiobuttons to the right. You can also use keyboard shortcuts, e.g. press `1` to select the first label
3. Play audio by pressing `Play audio`
4. `Left click-drag-release` to label a segment
5. You can also listen to just a part of the audiofile. To do this, `right click-drag-release` to select the audio portion and then `Play audio`
6. Press `Export` to export the labels. The labels are exported to a file `segmentations.xlsx` in the working directory

## Select audio with right click-drag-release
<img width="1645" alt="Screenshot 2022-12-17 at 13 00 57" src="https://user-images.githubusercontent.com/19154758/208238494-a87d2236-4fd9-4097-879b-84f9621ecbe7.png">

## Label audio with left click-drag-release
<img width="1673" alt="Screenshot 2022-12-17 at 12 59 08" src="https://user-images.githubusercontent.com/19154758/208238448-d167e550-0574-4110-bf9e-e9446b5bc00d.png">

## Exported labels in .xlsx
<img width="627" alt="output" src="https://user-images.githubusercontent.com/19154758/208238325-3ba6ba0b-caf2-4c9e-9c66-9afa5e4f642d.png">
