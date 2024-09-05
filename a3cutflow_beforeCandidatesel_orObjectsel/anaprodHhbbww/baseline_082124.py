from Common.Utilities import *
#yumeng:
#from Common.Setup import Setup

channels = [ 'muMu', 'eMu', 'eE' ] # in order of importance during the channel selection
leg_names = [ "Electron", "Muon" ]

def getChannelLegs(channel):
    ch_str = channel.lower()
    legs = []
    while len(ch_str) > 0:
        name_idx = None
        obj_name = None
        for idx, obj in enumerate([ 'e', 'mu' ]):
            if ch_str.startswith(obj):
                name_idx = idx
                obj_name = obj
                break
        if name_idx is None:
            raise RuntimeError(f"Invalid channel name {channel}")
        legs.append(leg_names[name_idx])
        ch_str = ch_str[len(obj_name):]
    return legs

def PassGenAcceptance(df):
    df = df.Filter("genHttCandidate.get() != nullptr", "genHttCandidate present")
    return df.Filter("PassGenAcceptance(*genHttCandidate)", "genHttCandidate Acceptance")

def GenJetSelection(df):
    df = df.Define("GenJet_B1","GenJet_pt > 20 && abs(GenJet_eta) < 2.5 && GenJet_Hbb")
    df = df.Define("GenJetAK8_B1","GenJetAK8_pt > 170 && abs(GenJetAK8_eta) < 2.5 && GenJetAK8_Hbb")
    #return df.Filter("GenJet_idx[GenJet_B1].size()==2 || (GenJetAK8_idx[GenJetAK8_B1].size()==1 && genHbb_isBoosted)", "(One)Two b-parton (Fat)jets at least")
    #yumeng
    df=df.Filter("GenJet_idx[GenJet_B1].size()==2 || (GenJetAK8_idx[GenJetAK8_B1].size()==1 && genHbb_isBoosted)", "GenJet_(1)2b(Fat)jets")
    return df

def GenJetHttOverlapRemoval(df):
    for var in ["GenJet", "GenJetAK8"]:
        df = df.Define(f"{var}_B2", f"RemoveOverlaps({var}_p4, {var}_B1,{{{{genHttCandidate->leg_p4[0], genHttCandidate->leg_p4[1]}},}}, 2, 0.5)" )
    return df.Filter("GenJet_idx[GenJet_B2].size()==2 || (GenJetAK8_idx[GenJetAK8_B2].size()==1 && genHbb_isBoosted)", "No overlap between genJets and genHttCandidates")

def RequestOnlyResolvedGenJets(df):
    return df.Filter("GenJet_idx[GenJet_B2].size()==2", "Resolved topology")

#yumeng:
def GenSelection(df,global_params):
#def GenSelection(df,setup):
#def GenSelection(df):
    df=df.Define("H_to_VV", """GetGenHVVCandidate(event, genLeptons, GenPart_pdgId, GenPart_daughters, GenPart_statusFlags, GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass, GenJet_p4, true)""")
    df=df.Define("GenLep1_p4","H_to_VV.legs.at(0).leg_vis_p4.at(0)")
    
    #if setup.global_params["my_channel"]== "slmuon":
    if global_params["my_channel"]== "slmuon":
        df=df.Filter("H_to_VV.legs.at(0).leg_kind.at(0)==Vleg::PromptMuon|| H_to_VV.legs.at(0).leg_kind.at(0)==Vleg::TauDecayedToMuon", "GenSLMu")
        df=df.Filter("GenLep1_p4.pt()>15 && abs (GenLep1_p4.eta()) <2.4", "GenMuAccept")

    if global_params["my_channel"]== "sle":
        df=df.Filter("H_to_VV.legs.at(0).leg_kind.at(0)==Vleg::PromptElectron|| H_to_VV.legs.at(0).leg_kind.at(0)==Vleg::TauDecayedToElectron", "GenSLe")
        df=df.Filter("GenLep1_p4.pt()>10 && abs (GenLep1_p4.eta()) <2.5", "Gen_e_Accept")
    
    return df

def RecoHWWCandidateSelection(df):
    #yumeng:
    df = df.Define("Electron_selp4", """v_ops::pt(Electron_p4) > 10""")
    #df = df.Define("N_sel_Ele_p4", "Electron_pt[Electron_selp4].size()")
    #df = df.Define("is_SLe_p4", "N_sel_lep == 1")

    df = df.Define("Muon_selp4", """v_ops::pt(Muon_p4) > 10""")
    df = df.Define("N_sel_Mu_p4", "Muon_pt[Muon_selp4].size()")

    #df = df.Define("Electron_sel", f"""Electron_selp4 &&  """)
    #df = df.Define("Muon_sel", f"""(Muon_selp4 && )""")

    df = df.Define("Electron_presel", """
        v_ops::pt(Electron_p4) > 10 && abs(v_ops::eta(Electron_p4)) < 2.5 && abs(Electron_dz) < 0.1 && abs(Electron_dxy) < 0.05 && Electron_sip3d <= 8 && Electron_miniPFRelIso_all < 0.4 && Electron_mvaIso_WP90""")

    df = df.Define("Muon_presel", """
        v_ops::pt(Muon_p4) > 15 && abs(v_ops::eta(Muon_p4)) < 2.4 && abs(Muon_dz) < 0.1 && abs(Muon_dxy) < 0.05 && abs(Muon_dxy) < 0.05 && Muon_sip3d <= 8 && Muon_miniPFRelIso_all < 0.4 && Muon_looseId""")

    df = df.Define("Electron_sel", f"""
        Electron_presel && Electron_mvaIso_WP80 """)

    df = df.Define("Muon_sel", f"""
        (Muon_presel && (Muon_tightId || Muon_highPtId ))""")
    
    df = df.Define("N_sel_Ele", "Electron_pt[Electron_sel].size()")
    df = df.Define("N_sel_Mu", "Muon_pt[Muon_sel].size()")
    df = df.Define("N_sel_lep", "N_sel_Ele + N_sel_Mu")

    df = df.Define("is_SL", "N_sel_lep == 1")
    df = df.Define("is_DL", "N_sel_lep >= 2")  
    
    #df = df.Filter("is_SL ? (N_sel_lep == 1) : (N_sel_lep >= 2);", "lepton selection")
    print("Yumeng")
    df = df.Filter("is_SL ? (N_sel_lep == 1) : (N_sel_lep >= 2);", "")

    df = df.Define("lep1_p4", "if (N_sel_Mu > 0) return Muon_p4[Muon_sel][0]; return Electron_p4[Electron_sel][0];")
    df = df.Define("lep1_type", "if (N_sel_Mu > 0) return 1; return 0;")

    df = df.Define("lep2_p4", """if (N_sel_Mu > 1) return Muon_p4[Muon_sel][1];
                                 if (N_sel_Ele > 1) return Electron_p4[Electron_sel][1];
                                 if (N_sel_Mu == 1 && N_sel_Ele == 1) return Electron_p4[Electron_sel][0];
                                 return LorentzVectorM(); """)
    df = df.Define("lep2_type", """if (N_sel_Mu > 1) return 1;
                                   if (N_sel_Ele > 1) return 0;
                                   if (N_sel_Mu == 1 && N_sel_Ele == 1) return 0;
                                   return -1; """)

    #yumeng:
    # if global_params["my_channel"]== "slmuon":
    #df=df.Filter("lep1_type==1 && lep2_type==-1", "SLMu")

    #if global_params["my_channel"]== "sle":
        #df=df.Filter("lep1_type==0 && lep2_type==-1", "SLe")

    return df

def RecoHWWJetSelection(df):
    df = df.Define("Jet_Incl", f"v_ops::pt(Jet_p4)>20 && abs(v_ops::eta(Jet_p4)) < 2.5 && ( Jet_jetId & 2 )")
    df = df.Define("FatJet_Incl", "(v_ops::pt(FatJet_p4)>200 && abs(v_ops::eta(FatJet_p4)) < 2.5 ) && ( FatJet_jetId & 2 ) && (FatJet_msoftdrop > 30 && FatJet_msoftdrop < 210)")#&& (FatJet_tau2 / FatJet_tau1 < 0.75)
    df = df.Define("Jet_sel", """if (is_SL)
                                    return RemoveOverlaps(Jet_p4, Jet_Incl,{ {lep1_p4, },}, 1, 0.5);
                                 return RemoveOverlaps(Jet_p4, Jet_Incl,{ {lep1_p4, lep2_p4},}, 2, 0.5); """)
    df = df.Define("FatJet_sel", """if (is_SL)
                                    return RemoveOverlaps(FatJet_p4, FatJet_Incl,{ {lep1_p4, },}, 1, 0.5);
                                 return RemoveOverlaps(FatJet_p4, FatJet_Incl,{ {lep1_p4, lep2_p4},}, 2, 0.5); """)

    df = df.Define("n_Jet_Sel", "Jet_p4[Jet_sel].size()")
    df = df.Define("n_FatJet_Sel", "FatJet_p4[FatJet_sel].size()")

    df = df.Define("Boosted_SL","(is_SL && (FatJet_p4[FatJet_sel].size()>=1) && (Jet_p4[Jet_sel].size()>=1))")
    df = df.Define("Resolved_SL","(is_SL && (FatJet_p4[FatJet_sel].size()==0) && (Jet_p4[Jet_sel].size()>=3))")
    df = df.Define("Boosted_DL","(is_DL && (FatJet_p4[FatJet_sel].size()>=1))")
    df = df.Define("Resolved_DL","(is_DL && (FatJet_p4[FatJet_sel].size()>=1) && (Jet_idx[Jet_sel].size()>=2))")
    return df.Filter(" is_SL ? (Boosted_SL || Resolved_SL ) : (Boosted_DL || Resolved_DL);", "Reco bjet candidates")

def RecoHttCandidateSelection(df, config):
    df = df.Define("Electron_B0", f"""
        v_ops::pt(Electron_p4) > 10 && abs(v_ops::eta(Electron_p4)) < 2.5 && abs(Electron_dz) < 0.2 && abs(Electron_dxy) < 0.045  """) # && (Electron_mvaIso_WP90 || (Electron_mvaNoIso_WP90 && Electron_pfRelIso03_all < 0.5))

    df = df.Define("Muon_B0", f"""
        v_ops::pt(Muon_p4) > 15 && abs(v_ops::eta(Muon_p4)) < 2.4 && abs(Muon_dz) < 0.2 && abs(Muon_dxy) < 0.045
        """) # && ( ((Muon_tightId || Muon_mediumId) && Muon_pfRelIso04_all < 0.5) || (Muon_highPtId && Muon_tkRelIso < 0.5) )


    df = df.Define("Electron_iso", "Electron_pfRelIso03_all") \
           .Define("Muon_iso", "Muon_pfRelIso04_all")

    df = df.Define("Muon_B2_muMu_1", f"""
        Muon_B0 && ( (Muon_tightId && Muon_pfRelIso04_all < 0.15) || (Muon_highPtId && Muon_tkRelIso < 0.15) )
    """)
    df = df.Define("Muon_B2_muMu_2", f"""
        Muon_B0 && ( (Muon_tightId && Muon_pfRelIso04_all < 0.3) || (Muon_highPtId && Muon_tkRelIso < 0.3) )
    """)

    df = df.Define("Electron_B2_eMu_1",f"Electron_B0 && Electron_mvaIso_WP80 ")
    #  Electron_mvaNoIso_WP80 && Electron_pfRelIso03_all < 0.3
    df = df.Define("Muon_B2_eMu_2", f"""
        Muon_B0 && ( (Muon_tightId && Muon_pfRelIso04_all < 0.3) || (Muon_highPtId && Muon_tkRelIso < 0.3) )
    """)

    df = df.Define("Electron_B2_eE_1",f"Electron_B0 && Electron_mvaIso_WP80 ")
    #  Electron_mvaNoIso_WP80 && Electron_pfRelIso03_all < 0.3
    df = df.Define("Electron_B2_eE_2", f""" Electron_B0 && Electron_mvaNoIso_WP80 && Electron_pfRelIso03_all < 0.3 """)

    cand_columns = []
    for ch in channels:
        leg1, leg2 = getChannelLegs(ch)
        cand_column = f"HttCandidates_{ch}"
        df = df.Define(cand_column, f"""
            GetHTTCandidates<2>(Channel::{ch}, 0.5, {leg1}_B2_{ch}_1, {leg1}_p4, {leg1}_iso, {leg1}_charge, {leg1}_genMatchIdx,{leg2}_B2_{ch}_2, {leg2}_p4, {leg2}_iso, {leg2}_charge, {leg2}_genMatchIdx)
        """)
        cand_columns.append(cand_column)
    cand_filters = [ f'{c}.size() > 0' for c in cand_columns ]
    stringfilter = " || ".join(cand_filters)
    df = df.Filter(" || ".join(cand_filters), "Reco Baseline 2")
    cand_list_str = ', '.join([ '&' + c for c in cand_columns])
    return df.Define('HttCandidate', f'GetBestHTTCandidate<2>({{ {cand_list_str} }}, event)')

# can remove
def ThirdLeptonVeto(df):
    df = df.Define("Electron_vetoSel",
                   f"""v_ops::pt(Electron_p4) > 10 && abs(v_ops::eta(Electron_p4)) < 2.5 && abs(Electron_dz) < 0.2 && abs(Electron_dxy) < 0.045
                      && ( Electron_mvaIso_WP90 == true )
                     && (HttCandidate.isLeg(Electron_idx, Leg::e)== false)""") # || ( Electron_mvaNoIso_WP90 && Electron_pfRelIso03_all<0.3) --> removed
    df = df.Filter("Electron_idx[Electron_vetoSel].size() == 0", "No extra electrons")
    df = df.Define("Muon_vetoSel",
                   f"""v_ops::pt(Muon_p4) > 10 && abs(v_ops::eta(Muon_p4)) < 2.4 && abs(Muon_dz) < 0.2 && abs(Muon_dxy) < 0.045
                      && ( Muon_mediumId || Muon_tightId ) && Muon_pfRelIso04_all<0.3
                      && (HttCandidate.isLeg(Muon_idx, Leg::mu) == false)""")
    df = df.Filter("Muon_idx[Muon_vetoSel].size() == 0", "No extra muons")
    return df

def RecoJetSelection(df):
    df = df.Define("Jet_bIncl", f"v_ops::pt(Jet_p4)>20 && abs(v_ops::eta(Jet_p4)) < 2.5 && ( Jet_jetId & 2 )")
    df = df.Define("FatJet_bbIncl", "FatJet_msoftdrop > 30 && abs(v_ops::eta(FatJet_p4)) < 2.5")
    df = df.Define("Jet_bCand", "RemoveOverlaps(Jet_p4, Jet_bIncl,{ {HttCandidate.leg_p4[0], HttCandidate.leg_p4[1]},}, 2, 0.5)")
    df = df.Define("FatJet_bbCand", "RemoveOverlaps(FatJet_p4, FatJet_bbIncl, { {HttCandidate.leg_p4[0], HttCandidate.leg_p4[1]},}, 2, 0.5)")
    return df

def ExtraRecoJetSelection(df):
    df = df.Define("ExtraJet_B0", f"v_ops::pt(Jet_p4)>20 && abs(v_ops::eta(Jet_p4)) < 5 && ( Jet_jetId & 2 )")
    df = df.Define(f"ObjectsToRemoveOverlap", "if(Hbb_isValid){return std::vector<RVecLV>({{HttCandidate.leg_p4[0], HttCandidate.leg_p4[1],HbbCandidate->leg_p4[0],HbbCandidate->leg_p4[1]}}); } return std::vector<RVecLV>({{HttCandidate.leg_p4[0], HttCandidate.leg_p4[1]}})")
    df = df.Define(f"ExtraJet_B1", """ RemoveOverlaps(Jet_p4, ExtraJet_B0,ObjectsToRemoveOverlap, 2, 0.5)""")
    return df


def ApplyJetSelection(df):
    return df.Filter("Jet_idx[Jet_bCand].size()>=2 || FatJet_idx[FatJet_bbCand].size()>=1", "Reco bjet candidates")

def GenRecoJetMatching(df):
    df = df.Define("Jet_genJetIdx_matched", "GenRecoJetMatching(event,Jet_idx, GenJet_idx, Jet_bCand, GenJet_B2, GenJet_p4, Jet_p4 , 0.3)")
    df = df.Define("Jet_genMatched", "Jet_genJetIdx_matched>=0")
    return df.Filter("Jet_genJetIdx_matched[Jet_genMatched].size()>=2", "Two different gen-reco jet matches at least")

def DefineHbbCand(df):
    df = df.Define("HbbCandidate", "GetHbbCandidate(Jet_btagDeepFlavB, Jet_bCand, Jet_p4, Jet_idx)")
    return df
