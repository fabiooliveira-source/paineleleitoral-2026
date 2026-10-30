"""Núcleo testável de regressão ponderada com padronização exclusiva do treino."""
import numpy as np

def fit_predict(features,y,w,train,dummies):
 n=len(features);means=features[train].mean(axis=0);sd=features[train].std(axis=0);sd=np.where(sd<1e-10,1,sd);a=np.column_stack([np.ones(n),(features-means)/sd,dummies]);weights=w[train]/w[train].sum();ata=a[train].T@(weights[:,None]*a[train]);aty=a[train].T@(weights*y[train]);ridge=np.eye(a.shape[1])*1e-6;ridge[0,0]=0;beta=np.linalg.solve(ata+ridge,aty);pred=np.clip(a@beta,0,1)
 return pred,{'coefficients_pp_per_sd':(100*beta[1:1+features.shape[1]]).tolist(),'means':means.tolist(),'std':sd.tolist(),'uf_effects_pp':(100*beta[1+features.shape[1]:]).tolist(),'intercept_pct':float(100*beta[0])}
