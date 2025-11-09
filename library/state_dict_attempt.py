import torch

from sequence_labeller import SequenceLabeller

model = SequenceLabeller.load("/Users/nathanwolf/Documents/Coding/HackTuah2025/MorphSeg/library/pretrained_models/eng.pt",torch.cpu.current_device())
torch.save(model.model[0].state_dict(),"/Users/nathanwolf/Documents/Coding/HackTuah2025/MorphSeg/library/testmorphseg/non_spacy/pretrained_models/eng.pt")