from pathlib import Path
from tqdm import tqdm

import torch 
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sn

from utils import parse_config
from models.build import build_model_from_config
from data_loader.data_loader import get_data_loaders_from_config

def test_model(model, dataloader, config, classes=None):
    device = config['training']['device']
    
    # Initialize the prediction and label lists(tensors)
    predlist=torch.zeros(0,dtype=torch.long, device='cpu')
    lbllist=torch.zeros(0,dtype=torch.long, device='cpu')

    model.eval()
    for step, data in enumerate(tqdm(dataloader)):
        inputs, labels = data
        inputs = inputs.to(device)
        labels = labels.to(device)
        
        with torch.no_grad():
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

        # Append batch prediction results
        predlist=torch.cat([predlist,preds.cpu()])
        lbllist=torch.cat([lbllist,labels.cpu()])
        # predlist=torch.cat([predlist,preds.view(-1).cpu()])
        # lbllist=torch.cat([lbllist,labels.view(-1).cpu()])

    labels_np = lbllist.numpy()
    preds_np = predlist.numpy()

    conf_mat=confusion_matrix(labels_np, preds_np)
    print(conf_mat)
    report = classification_report(lbllist, preds_np, target_names=classes)
    print(report)
    return conf_mat, report

def main(args):
    config = parse_config(args.config)

    out_dir = Path(config['training']['save_dir']) / config['training']['save_context'] 
    out_dir.mkdir(exist_ok=True, parents=True)

    model = build_model_from_config(config)
    dataloaders, classes = get_data_loaders_from_config(config)
    conf_mat, report = test_model(model, dataloaders['test'], config,  classes=classes)

    test_dir = out_dir / 'test'
    test_dir.mkdir(exist_ok=True, parents=True)
    test_out  = test_dir /  f"{config['training']['save_context']}_clfreport.log"
    with test_out.open('w') as wf:
        wf.write(report)

    sn_plot = sn.heatmap(conf_mat, annot=True, fmt='g', xticklabels=classes, yticklabels=classes)
    test_out_cm  = test_dir /  f"{config['training']['save_context']}_confmat.jpg"
    sn_plot.get_figure().savefig(test_out_cm)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', help='Path to config file', default='configs/test-config.yaml')
    args = ap.parse_args()

    main(args)