"""utilities - PADL - GTAR - London, JPMorgan"""
import sys
import os
from pathlib import Path

path = os.path.realpath(__file__)
parent_dir = str(Path(path).parents[1])
sys.path.append(parent_dir)

import json
import numpy as np
from pyledger.zkutils import Secp256k1

# try to
class InjectiveUtils():
    @staticmethod
    def get_four_squares(x):
        """
        function to find numbers whose squares sum up to x = v1^2 + v2^2 + v3^2+ v4^2
        :param x: any integer
        :return: four integers whose squares sum up to x
        """
        xd = int(np.ceil(np.sqrt(x)))
        for i in range(0,xd):
            for j in range(0,xd):
                for l in range(0,xd):
                    for m in range(0,xd):
                        if i*i + j*j + l*l + m*m == x:
                            return (i,j,l,m)
        return(0,0,0,0)

    @staticmethod
    def format_range_proof_positive_commitment(rpr):
        useful_keys_point = {'cm1':'cm1',
                             'cm2':'cm2',
                             'cm3':'cm3',
                             'chalRspDg':'chalRspDg',
                             'chalRspD1h':'chalRspD1h',
                             'challengecm2':'challengecm2',
                             'chalRspDcm2':'chalRspDcm2',
                             'chalRspD2h':'chalRspD2h',
                             'challengecm3':'challengecm3'}

        useful_keys_scalar = {'challenge':'challenge',
                              'challenge_response_D':'chalRspD',
                              'challenge_response_D1':'chalRspD1',
                              'challenge_response_D2':'chalRspD2'}
        useful_pr_point = {useful_keys_point[key]:Secp256k1.get_xy(rpr[key]['point']) for key in useful_keys_point.keys()}
        useful_pr_scalar = {useful_keys_scalar[key]:int('0x'+rpr[key]['scalar'],16) for key in useful_keys_scalar.keys()}
        useful_pr_point.update(useful_pr_scalar)
        return useful_pr_point

    @staticmethod
    def format_proofs(pr):
        pr = json.loads(pr)
        sol_pr = pr
        for key,values in pr.items():
            if 'scalar' in pr[key]:
                sol_pr[key] = int('0x' + pr[key]['scalar'],16)
            elif 'point' in pr[key]:
                sol_pr[key] = Secp256k1.get_xy(pr[key]['point'])
            else:
                sol_pr[key] = pr[key]
        return sol_pr


    @staticmethod
    def format_eq_proof(pr):
        pr = json.loads(pr)
        useful_keys_point = {'pk': 'pk',
                             'pk_t_rand_commitment':'pktrand',
                             'chalrsph2r':'chalrsph2r',
                             'challengepk':'challengepk'}

        useful_keys_scalar = {'challenge_response':'chalrsp'}
        useful_pr_point = {useful_keys_point[key]:Secp256k1.get_xy(pr[key]['point']) for key in useful_keys_point.keys()}
        useful_pr_scalar = {useful_keys_scalar[key]:int('0x'+pr[key]['scalar'],16) for key in useful_keys_scalar.keys()}
        useful_pr_point.update(useful_pr_scalar)
        return useful_pr_point

    @staticmethod
    def format_consistency_proof(P_C, cm, token, pubkey):
        pc = json.loads(P_C)
        pc['cm'] = Secp256k1.get_xy(cm)
        pc['tk'] = Secp256k1.get_xy(token)
        pc['pubkey'] = Secp256k1.get_xy(pubkey)
        return json.dumps(pc)


    @staticmethod
    def format_tx_to_solidity(tx):
        """
        formats a transaction to solidity transaction structure
        :param tx: PADL transaction
        :return: PADL transaction as defined on smart contract 'PADLOnChain.sol'
        """
        txsol = []
        compcm = ""
        comptk = ""
        eqp = ""
        comppc = ""
        for a in range(0,len(tx)):
            for p in range(0,len(tx[a])):
                if tx[a][p].cm_:
                    eqp = tx[a][p].P_A[1]
                    compcm = Secp256k1.get_xy(tx[a][p].cm_)
                    comptk = Secp256k1.get_xy(tx[a][p].token_)
                    comppc = tx[a][p].P_C_

        for a in range(0,len(tx)):
            for p in range(0,len(tx[a])):
                if tx[a][p].cm_:
                    txsol.append({'cm':Secp256k1.get_xy(tx[a][p].cm),
                                  'tk':Secp256k1.get_xy(tx[a][p].token),
                                  'compcm': compcm,
                                  'comptk':comptk,
                                  'ppositive':tx[a][p].P_A[0],
                                  'pc': InjectiveUtils.format_proofs(tx[a][p].P_C),
                                  'peq':InjectiveUtils.format_eq_proof(eqp),
                                  'pc_':InjectiveUtils.format_proofs(tx[a][p].P_C_)})
                else:
                    txsol.append({'cm':Secp256k1.get_xy(tx[a][p].cm),
                                  'tk':Secp256k1.get_xy(tx[a][p].token),
                                  'compcm': compcm,
                                  'comptk':comptk,
                                  'ppositive':tx[a][p].P_A,
                                  'pc': InjectiveUtils.format_proofs(tx[a][p].P_C),
                                  'peq':InjectiveUtils.format_eq_proof(eqp),
                                  'pc_':InjectiveUtils.format_proofs(comppc)})
        return txsol
    
    @staticmethod
    def check_tx_structure(tx, send_ID):
            """Check the structure (data type and variable length)
            Args:
                tx (list): a list of transactions
                vals (list): a list of asset
            """
            result = []
            for i in range(len(tx)):
                for id,v in enumerate(tx[i]):
                    result.append(InjectiveUtils.check_help(tx[i][id], id, send_ID))
            return all(res==True for res in result)

 
    @staticmethod
    def check_help(tx, id, send_ID):
            """help function to check the type and ;ength of each variable in tx
            Args:
                tx (object): one transaction object
                id (int): the index number of asset in vals[i]
            """
            # there are both a solidity and rust version for the checking structure
            type_checks_seid = [ #('P_A[0]', dict, 'asset type is wrong'), #solidity
                #('P_A[1]', str, 'eqpr type is wrong'), #solidity
                ('P_A', list, 'rpr type is wrong'), #rust
                ('P_C_', str, 'complimentary consistency type is wrong'),
                ('cm_', str, 'complimentary commit type is wrong', 66),
                ('token_', str, 'complimentary token type is wrong', 66),
                #('P_Eq', str, 'proof of Eq type is wrong')]
                # for common variables
                ('P_C', str, 'consistency type is wrong'),
                ('cm', str, 'commit type is wrong', 66),
                ('token', str, 'token type is wrong', 66)]

            type_checks_Nseid = [ #('P_A', dict, 'asset type is wrong'), #solidity
                ('P_A', list, 'asset type is wrong'), #rust
                # for common variables
                ('P_C', str, 'consistency type is wrong'),
                ('cm', str, 'commit type is wrong', 66),
                ('token', str, 'token type is wrong', 66)]

            if send_ID==id:
                type_checks = type_checks_seid
            else:
                type_checks= type_checks_Nseid

            for name, err_type, error_tx, *length in type_checks:
                value = getattr(tx, name, None)
                if not isinstance(value,err_type) or (length and len(value)!=length[0]):
                    print(f'The transaction proof of {error_tx}')
                    return False

            return True
