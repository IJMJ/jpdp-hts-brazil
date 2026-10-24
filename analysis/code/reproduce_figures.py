from pathlib import Path
import sys, csv, json
from collections import Counter
import textwrap
R=Path(__file__).resolve().parents[1]

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
I=R/'data';O=R/'results/figures';O.mkdir(parents=True,exist_ok=True)
e=list(csv.DictReader((I/'entity_master_R1_coverage_working.csv').open()))
a=list(csv.DictReader((I/'article_reporting_scores_R1_working.csv').open()))
s=json.loads((R/'reference/expected_results.json').read_text());n=len(e)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','savefig.facecolor':'white','axes.titleweight':'bold'})
blue='#176A8A';orange='#CD8234';gray='#B8C4CD'
def save(fig,k):
    fig.savefig(O/f'Fig{k}_R1.png',dpi=300,bbox_inches='tight',pad_inches=.1)
    fig.savefig(O/f'Fig{k}_R1.svg',bbox_inches='tight',pad_inches=.1)
    plt.close(fig)
def finish(ax):ax.set_axisbelow(True);ax.grid(axis='x',alpha=.17)

fig,ax=plt.subplots(figsize=(7.2,8.4));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
def box(x,y,w,h,label,color='#EEF4F7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.009',linewidth=.8,edgecolor='#536C7B',facecolor=color))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10,linespacing=1.25)
def arrow(x,y,z,t):ax.annotate('',xy=(z,t),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#536C7B','lw':1})
ax.text(.5,.98,'Historical search and selection',ha='center',va='top',fontsize=13,fontweight='bold')
box(.02,.82,.45,.105,'PubMed\n314 query hits\n282 unique records')
box(.53,.82,.45,.105,'Europe PMC expansion\n9,144 records\n176 overlap with PubMed')
box(.53,.64,.45,.12,'8,968 classifier inputs\n85 advanced to screening\n8,883 not forwarded')
arrow(.755,.82,.755,.76)
box(.02,.455,.96,.14,'367 manually screened: 275 excluded / 30 supporting\n48 preliminarily eligible / 14 for full-text resolution\nAfter full text: 58 eligible / 8 not retained at entity adjudication\nOriginal evidence set: 50 articles / 63 entities')
arrow(.245,.82,.245,.595);arrow(.755,.64,.755,.595)
ax.text(.5,.43,'Checks performed during revision',ha='center',va='center',fontsize=13,fontweight='bold')
box(.02,.23,.45,.15,'Historical non-forwarded queue\n141 records examined\nOther 8,742 not validated\nDirected source reconciliation','#F7F1E9')
box(.53,.23,.45,.15,'L02 current-index retrieval\n5,421 records on 20 Oct 2026\n5,056 linked / 365 unlinked\nInitial screen + directed checks','#F7F1E9')
box(.02,.035,.96,.12,'Revised evidence set\n65 articles / 129 entities / 139 links\nMain cohort 77 / Secondary cohort 52')
arrow(.245,.23,.245,.155);arrow(.755,.23,.755,.155)
save(fig,1)

fig,axs=plt.subplots(2,1,figsize=(7.2,7.2),gridspec_kw={'height_ratios':[1,1.3]})
years=list(range(2016,2027));ca=Counter(int(x['year']) for x in a);ce=Counter(int(x['publication_year_numeric']) for x in e)
x=np.arange(len(years));axs[0].bar(x-.19,[ca[y] for y in years],.38,label='Articles',color=blue);axs[0].bar(x+.19,[ce[y] for y in years],.38,label='Entities',color=orange)
axs[0].set_xticks(x,years,rotation=45);axs[0].set_ylabel('Count');axs[0].set_title('a  Publication year',loc='left');axs[0].legend(frameon=False,ncol=2);axs[0].grid(axis='y',alpha=.17);axs[0].set_axisbelow(True)
c=s['contribution_counts'];labels=[textwrap.fill(k,32) for k in c];vals=list(c.values());y=np.arange(len(c));axs[1].barh(y,vals,color=blue);axs[1].set_yticks(y,labels,fontsize=9);axs[1].invert_yaxis();axs[1].set_xlabel('Entities');axs[1].set_xlim(0,max(vals)*1.13)
for j,v in enumerate(vals):axs[1].text(v+.7,j,str(v),va='center')
axs[1].set_title('b  Primary contribution',loc='left');finish(axs[1]);fig.tight_layout(h_pad=2);save(fig,2)

families=sorted(s['family_counts'],key=lambda k:(-s['family_counts'][k],k))
hosts=sorted({x['host_system_group'] for x in e})
fig,axs=plt.subplots(2,1,figsize=(7.6,10.1),gridspec_kw={'height_ratios':[1,1.15]})
y=np.arange(len(families));yes=[sum(x['family_display']==f and x['species_status']=='Accepted species' for x in e) for f in families];no=[s['family_counts'][f]-yes[j] for j,f in enumerate(families)]
axs[0].barh(y,yes,color=blue,label='Accepted species');axs[0].barh(y,no,left=yes,color=gray,label='No accepted species')
axs[0].set_yticks(y,families,fontsize=9.3);axs[0].invert_yaxis();axs[0].set_xlabel('Entities');axs[0].set_title('a  Formal family and species status',loc='left');axs[0].legend(frameon=False,fontsize=9,loc='lower right');finish(axs[0])
matrix=np.array([[sum(x['family_display']==f and x['host_system_group']==h for x in e) for h in hosts] for f in families]);mask=np.ma.masked_where(matrix==0,matrix)
axs[1].imshow(mask,cmap='Blues',vmin=0,vmax=max(matrix.max(),1),aspect='auto')
axs[1].set_yticks(y,families,fontsize=9.3);axs[1].set_xticks(np.arange(len(hosts)),hosts,rotation=58,ha='right',fontsize=8.3)
axs[1].set_ylabel('Formal family / unresolved family');axs[1].set_xlabel('Standardized host-system category');axs[1].set_title('b  Family by host-system category',loc='left')
for j in range(len(families)):
    for k in range(len(hosts)):
        if matrix[j,k]:axs[1].text(k,j,str(matrix[j,k]),ha='center',va='center',fontsize=8.5,color='white' if matrix[j,k]>matrix.max()*.5 else '#172B37')
fig.tight_layout(h_pad=2);save(fig,3)

metrics={(x['cohort'],x['metric']):x for x in s['entity_metrics']}
fig,axs=plt.subplots(3,1,figsize=(7.2,8.5),gridspec_kw={'height_ratios':[1,1,1.1]})
names=['Inventory','Molecular validation','Replicated association','Experimental infection','Disease reproduction','Reconstructed agent']
vals=[129,106,69,17,7,3];y=np.arange(6);axs[0].barh(y,vals,color=[gray,blue,blue,blue,orange,orange]);axs[0].set_yticks(y,names);axs[0].invert_yaxis();axs[0].set_xlim(0,145);axs[0].set_xlabel('Entities')
for j,v in enumerate(vals):axs[0].text(v+1,j,str(v),va='center')
axs[0].set_title('a  Biological evidence milestones',loc='left');finish(axs[0])
cl=['B0','B1','B2','B3','B4','B5'];tot=[s['strongest_evidence_counts'][k] for k in cl];rr=[sum(x['strongest_biological_evidence_class']==k and x['has_public_raw_reads']=='1' for x in e) for k in cl]
xx=np.arange(6);axs[1].bar(xx,tot,color=gray,label='All entities');axs[1].bar(xx,rr,color=blue,label='Confirmed public raw reads');axs[1].set_xticks(xx,cl);axs[1].set_ylabel('Entities');axs[1].legend(frameon=False,fontsize=9);axs[1].set_title('b  Strongest class and public raw reads',loc='left');axs[1].set_ylim(0,max(tot)*1.2)
for j,v in enumerate(tot):axs[1].text(j,v+.7,str(v),ha='center',fontsize=9)
for j,v in enumerate(rr):
    if v:axs[1].text(j,v/2,str(v),ha='center',va='center',color='white',fontsize=9)
keys=['complete_or_coding_complete_genome','accepted_species','hts_platform_explicit','state_level_mappable','experimental_infection_or_higher','has_public_raw_reads'];labels=['Complete / coding-complete','Accepted ICTV species','Explicit platform','State-level mappable','Experimental infection','Public raw reads']
for j,k in enumerate(keys):
    t=metrics['All',k];v=t['percent'];lo,hi=[100*z for z in t['wilson95']];axs[2].errorbar(v,j,xerr=[[v-lo],[hi-v]],fmt='o',color=blue,capsize=3);axs[2].text(101,j,f"{t['numerator']}/129",va='center',fontsize=9)
axs[2].set_yticks(np.arange(6),labels);axs[2].invert_yaxis();axs[2].set_xlim(0,117);axs[2].set_xticks([0,25,50,75,100]);axs[2].set_xlabel('Entities (%) with Wilson 95% interval');axs[2].set_title('c  Selected proportions',loc='left');finish(axs[2]);fig.tight_layout(h_pad=1.8);save(fig,4)

def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n;mid=(p+z*z/(2*n))/d;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return mid-h,mid+h
fig,axs=plt.subplots(2,1,figsize=(7.2,7.3),gridspec_kw={'height_ratios':[1,1.15]})
labels=['Total reads','Virus-supporting reads','Coverage depth','Preprocessing parameters','Assembly parameters','Mapping / identification']
colors=['#176A8A','#CD8234','#5C7750','#885D93','#AE535C','#737373']
for j,d in enumerate(s['temporal']['dimensions']):
    k=sum(d['reported_by_period']);lo,hi=wilson(k,65);v=k/65*100;axs[0].errorbar(v,j,xerr=[[v-100*lo],[100*hi-v]],fmt='o',color=blue,capsize=3);axs[0].text(89,j,f'{k}/65',va='center',fontsize=9)
    vals=np.array(d['reported_by_period'])/np.array(d['total_by_period'])*100
    axs[1].plot(range(3),vals,marker=['o','s','^','D','v','P'][j],label=labels[j],color=colors[j],linewidth=1.6)
axs[0].set_yticks(range(6),labels);axs[0].invert_yaxis();axs[0].set_xlim(0,103);axs[0].set_xticks([0,25,50,75,100]);axs[0].set_xlabel('Articles (%) with Wilson 95% interval');axs[0].set_title('a  Reporting across 65 articles',loc='left');finish(axs[0])
axs[1].set_xticks(range(3),['2016-2019\nn = 22','2020-2022\nn = 21','2023-2026\nn = 22']);axs[1].set_ylabel('Articles reporting (%)');axs[1].set_ylim(0,100);axs[1].set_title('b  Reporting by publication period',loc='left');axs[1].grid(axis='y',alpha=.17);axs[1].legend(frameon=False,fontsize=8.5,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.24))
fig.tight_layout(h_pad=2.5);save(fig,5)
(R/'results/figure_source_summary.json').write_text(json.dumps({'articles':65,'entities':129,'links':139,'figures':[1,2,3,4,5],'figure_3_host_labels_preserved':hosts,'figure_3_families':families,'no_new_statistical_test':True},indent=2)+'\n')
print('Five figures regenerated from the checked 65/129 dataset; original tests retained.')
