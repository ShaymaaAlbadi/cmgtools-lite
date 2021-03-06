import PhysicsTools.HeppyCore.framework.config as cfg
from PhysicsTools.HeppyCore.framework.config import printComps
from PhysicsTools.Heppy.utils.cmsswPreprocessor import CmsswPreprocessor

# Tau-tau analyzers
from CMGTools.H2TauTau.proto.analyzers.MuEleAnalyzer             import MuEleAnalyzer
from CMGTools.H2TauTau.proto.analyzers.H2TauTauTreeProducerMuEle import H2TauTauTreeProducerMuEle
from CMGTools.H2TauTau.proto.analyzers.DiLeptonWeighter            import DiLeptonWeighter
from CMGTools.H2TauTau.proto.analyzers.SVfitProducer              import SVfitProducer
from CMGTools.H2TauTau.proto.analyzers.LeptonIsolationCalculator import LeptonIsolationCalculator
from CMGTools.H2TauTau.proto.analyzers.FileCleaner import FileCleaner

# common configuration and sequence
from CMGTools.H2TauTau.htt_ntuple_base_cff import commonSequence, genAna, dyJetsFakeAna, puFileData, puFileMC, eventSelector

from CMGTools.RootTools.utils.splitFactor import splitFactor
from CMGTools.H2TauTau.proto.samples.fall15.triggers_muEle import mc_triggers, mc_triggerfilters, data_triggers, data_triggerfilters

from CMGTools.H2TauTau.proto.samples.fall15.htt_common import backgrounds_mu, sm_signals, mssm_signals, data_muon_electron, sync_list


# local switches
syncntuple   = True
computeSVfit = False
production   = False  # production = True run on batch, production = False run locally
cmssw = True
data = False

muonIsoCalc = cfg.Analyzer(
    LeptonIsolationCalculator,
    name='MuonIsolationCalculator',
    lepton='muon',
    getter=lambda event: [event.leg2]
)

electronIsoCalc = cfg.Analyzer(
    LeptonIsolationCalculator,
    name='ElectronIsolationCalculator',
    lepton='electron',
    getter=lambda event: [event.leg1]
)


dyJetsFakeAna.channel = 'em'

### Define mu-ele specific modules

muEleAna = cfg.Analyzer(
  MuEleAnalyzer                 ,
  'MuEleAnalyzer'               ,
  pt1          = 13.            ,
  eta1         = 2.5            ,
  iso1         = 0.15           ,
  looseiso1    = 9999.            ,
  pt2          = 10.            ,
  eta2         = 2.4            ,
  iso2         = 0.15           ,
  looseiso2    = 9999.            ,
  m_min        = 0.             ,
  m_max        = 99999          ,
  dR_min       = 0.3            ,
  from_single_objects=True,
  verbose      = False          ,
  )

leptonWeighter = cfg.Analyzer(
    DiLeptonWeighter,
    name='DiLeptonWeighter',
    scaleFactorFiles={
        'trigger_mu_low':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Muon_Mu8_fall15.root',
        'trigger_mu_high':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Muon_Mu17_fall15.root',
        'trigger_e_low':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Electron_Ele12_fall15.root',
        'trigger_e_high':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Electron_Ele17_fall15.root',
        'idiso_mu':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Muon_IdIso0p15_fall15.root',
        'idiso_e':'$CMSSW_BASE/src/CMGTools/H2TauTau/data/Electron_IdIso0p15_fall15.root',
    },
    lepton_e='leg1',
    lepton_mu='leg2',
    disable=False
)



treeProducer = cfg.Analyzer(
  H2TauTauTreeProducerMuEle         ,
  name = 'H2TauTauTreeProducerMuEle'
  )

syncTreeProducer = cfg.Analyzer(
  H2TauTauTreeProducerMuEle                     ,
  name         = 'H2TauTauSyncTreeProducerMuEle',
  varStyle     = 'sync'                         ,
#  skimFunction = 'event.isSignal'
  )

svfitProducer = cfg.Analyzer(
  SVfitProducer                ,
  name        = 'SVfitProducer',
  # integration = 'VEGAS'        ,
  integration = 'MarkovChain'  ,
  # verbose     = True           ,
  # order       = '21'           , # muon first, tau second
  l1type      = 'muon'         ,
  l2type      = 'ele'
  )

fileCleaner = cfg.Analyzer(
    FileCleaner,
    name='FileCleaner'
)


if cmssw:
    muEleAna.from_single_objects = False

samples = backgrounds_mu + sm_signals + mssm_signals + sync_list
#samples = backgrounds_mu + sm_signals

split_factor = 1e5

for sample in samples:
    sample.triggers = mc_triggers
    sample.triggerobjects = mc_triggerfilters
    sample.splitFactor = splitFactor(sample, split_factor)

data_list = data_muon_electron

for sample in data_list:
    sample.triggers = data_triggers
    sample.triggerobjects = data_triggerfilters
    sample.splitFactor = splitFactor(sample, split_factor)
    sample.json = '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions15/13TeV/Cert_246908-260627_13TeV_PromptReco_Collisions15_25ns_JSON_v2.txt'
    sample.lumi = 2300.


###################################################
###              ASSIGN PU to MC                ###
###################################################
for mc in samples:
    mc.puFileData = puFileData
    mc.puFileMC = puFileMC

###################################################
###             SET COMPONENTS BY HAND          ###
###################################################
#selectedComponents = samples
selectedComponents = samples + data_list
#selectedComponents = data_list
#selectedComponents = samples


###################################################
###                  SEQUENCE                   ###
###################################################
sequence = commonSequence
sequence.insert(sequence.index(genAna), muEleAna)
sequence.append(leptonWeighter)
if computeSVfit:
    sequence.append(svfitProducer)
sequence.append(treeProducer)
if syncntuple:
    sequence.append(syncTreeProducer)

sequence.insert(sequence.index(treeProducer), muonIsoCalc)
sequence.insert(sequence.index(treeProducer), electronIsoCalc)
treeProducer.addIsoInfo = True


if not syncntuple:
    module = [s for s in sequence if s.name == 'H2TauTauSyncTreeProducerTauMu'][0]
    sequence.remove(module)

if not cmssw:
    module = [s for s in sequence if s.name == 'MCWeighter'][0]
    sequence.remove(module)



###################################################
###             CHERRY PICK EVENTS              ###
###################################################
#eventSelector.toSelect = [370324]
#sequence.insert(0, eventSelector)

###################################################
###            SET BATCH OR LOCAL               ###
###################################################
if not production:
  cache                = True
  comp = sync_list[0]
  selectedComponents   = [comp]
  comp.splitFactor     = 5
  comp.fineSplitFactor = 1
#  comp.files           = comp.files[:1]

preprocessor = None
if cmssw:
    fname = "$CMSSW_BASE/src/CMGTools/H2TauTau/prod/h2TauTauMiniAOD_emu_data_cfg.py" if data else "$CMSSW_BASE/src/CMGTools/H2TauTau/prod/h2TauTauMiniAOD_emu_cfg.py"

    sequence.append(fileCleaner)
    preprocessor = CmsswPreprocessor(fname, addOrigAsSecondary=False)

# the following is declared in case this cfg is used in input to the
# heppy.py script
from PhysicsTools.HeppyCore.framework.eventsfwlite import Events
config = cfg.Config( components   = selectedComponents,
                     sequence     = sequence          ,
                     services     = []                ,
                     preprocessor=preprocessor,
                     events_class = Events
                     )

printComps(config.components, True)

def modCfgForPlot(config):
  config.components = []
