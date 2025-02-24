#!/usr/bin/env python2.7

'''
#Load process and store NR data for coprecessing frame modeling.
londonl@mit.edu 2020

## Outline

1. Load simulation 
2. Compute TD Psi4 Co-Precessing Frame 
3. Symmetrize the co-precessing frame data 
4. Output the symmetrized FD amplitude and phase along with diagnostic plots
'''

# Setup python environment
from matplotlib.pyplot import *
from numpy import *
from positive import *
from nrutils import scsearch, gwylm
from glob import glob
import h5py
from os import path
import pickle
import pwca
from mpa import gwylmo_cpclean

# Preliminaries 
# --

# Define path for file IO
package_dir = parent( pwca.__path__[0] )
data_dir = package_dir + 'data/version2/'
mkdir(data_dir,verbose=True)

# Find and load data
# --

# Define simulations to load
simulation_keywords = ('q1a04t30_dPm2_T_96_552', 'q1a04t60_dPm1_T_96_552', 'q1a04t90_dP0_T_96_552', 'q1a04t120_dP0_T_96_552', 'q1a04t150_dP0_T_96_552',  'q1a08t30dPm25_T_96_408', 'q1a08t60dPm1.5_T_96_408', 'q1a08t90dPm1_T_96_408', 'q1a08t120dP0_T_96_408', 'q1a08t150dP0_T_96_408', 'q2a04t30dPm2_T_96_408', 'q2a04t60dPm1_T_96_408', 'q2a04t90dPm1_T_96_408', 'q2a04t120_T_96_408', 'q2a04t150_T_96_408', 'q2_a10_a28_ph0_th30', 'q2_a10_a28_ph0_th60', 'q2_a10_a28_ph0_th90', 'q2_a10_a28_ph0_th120', 'q2_a10_a28_ph0_th150', 'q4a04t30_T_96_360', 'q4a04t60dPm1.5D_T_96_360', 'q4a04t90_T_96_360', 'q4a04t120dP0D_T_96_360', 'q4a04t150_T_96_360', 'q4a08t30dPm5p5dRm47_T_96_360', 'q4a08t60dPm3dRm250_T_96_384', 'q4a08t90dPm1D_T_96_384', 'q4a08t120dP1_T_96_360', 'q4a08t150_T_96_360',  'q8a04t30dPm3_T_96_360', 'q8a04t60D_dPm1', 'q8a04t90dP0_T_96_360', 'q8a04t120dPp1_T_96_360', 'q8a04t150dP9_T_96_360', 'q8a08t30dPm9.35_r0.5_T_96_360', 'q8a08t60Ditm45dr075_96_360', 'q8a08t90dP0_T_96_384', 'q8a08t120dP2_r03_T_96_360', 'q8a08t150dP2_T_120_480')

# Find select simulations using scsearch
A = scsearch( keyword=simulation_keywords, notkeyword=('80_Points','ASJmodified','.0.1.0','q8precessing/q8a04t60D_dPm1/'), verbose= True, unique=True )

#
catalog_path = '/Users/book/KOALA/puck/ll/data/pwca_catalog.pickle'
alert('Saving scentry catalog list to %s'%magenta(catalog_path))
pickle.dump( A, open( catalog_path, "wb" ) )

# Let the people know.
alert('We have found %i simulations.'%len(A))

# Define loading parameters 
lmax = 2
pad = 1000
clean = True
dt = 0.5

# Load and prcess simulations 
# --

# For all sims 
for a in A:
    
    #
    txt_file_path = data_dir+'%s.txt'%a.simname
    # if path.exists(txt_file_path):
    #     warning('It seems that %s already exists, so we\'re moving on ...'%magenta(txt_file_path),header=True)
    #     continue
    
    #
    alert('Processing: %s'%magenta(a.simname),header=True)
    
    # Load
    y_raw = gwylm(a,lmax=lmax,dt=dt,pad=pad,clean=clean,verbose=True)
    
    # Manage frames using dict defined below
    frame = {}
    frame['raw'] = y_raw

    # Put in initial J frame
    frame['init-j'] = y_raw.__calc_initial_j_frame__()
    # # # NOTE that although the angles model uses the j(t) frame, the do NOT use this here as the coprecessing frame is uniquely defined and the j(t) frame only adds problematic noise
    # # frame['j-of-t'] = frame['init-j'].__calc_j_of_t_frame__()
    
    # --
    # Compute waveforms that have been symmetrized in the psi4 coprecessing frame.
    # NOTE that we will tag these cases with "star"
    # --
    
    # Symmetrize the psi4 time domain coprecessing frame waveform, and return to the init-j frame
    frame['star-init-j'] = gwylmo_cpclean( frame['init-j'], cp_domain='td' )
    
    # Calculate the coprecessing frame for the case above
    # Compute TD adn FD coprecessing psi4 frames
    frame['star-sym-cp-y-fd'] = frame['star-init-j'].__calc_coprecessing_frame__( transform_domain='fd', kind='psi4' )
    frame['star-sym-cp-y-td'] = frame['star-init-j'].__calc_coprecessing_frame__( transform_domain='td', kind='psi4' )
    
    # Produce diagnostic plots 
    def plot_amp_dphi(frame):

        #
        fig = figure( figsize=4*figaspect(0.8) )

        #
        y0,y1 = -inf,1e4
        kind = 'psi4' # kind used to measure smoothness of phase derivate
        D0 = mean( frame['star-sym-cp-y-fd'][2,2][kind].fd_dphi )
        smoothness_measure = {}
        case_test = lambda k: ('star' in k) and ( not ('init' in k) )

        #
        for k in sort(frame.keys())[::-1]:

            #
            if case_test(k):

                f = frame[k].f
                mask = ((f)>0.02) & ((f)<0.06)
                this_smoothness_measure = abs( std( frame[k][2,2][kind].fd_dphi[mask]-smooth(frame[k][2,2][kind].fd_dphi[mask]).answer ) )
                smoothness_measure[k] = this_smoothness_measure 

        #
        for k in sort(frame.keys())[::-1]:

            #
            if case_test(k):

                #
                is_best = smoothness_measure[k]==min(smoothness_measure.values())

                #
                alp = 1 if 'star' in k else 0.14
                ls = ':' if not ('sym' in k) else '-'
                ls = '-.' if ('td' in k) and not ('star' in k) else ls
                lw = 2

                #
                ax1 = subplot(2,1,1)
                kind = 'strain'
                f = frame[k].f
                mask = abs(f)<0.1
                ln = plot( f, frame[k][2,2][kind].fd_amp, label=k, alpha=1 if is_best else 0.2, ls=ls if not is_best else '-', lw=lw if not is_best else 2 )
                #ln = plot( f, frame[k][2,2][kind].fd_amp, label=k, alpha=alp, ls=ls, lw=lw )
                ylabel(r'$|\tilde{h}_{22}|$')
                yscale('log')
                xlabel('$fM$')
                xscale('log')
                xlim( 0.008, 0.115 )
                ylim( 1e0,1e2 )
                legend(ncol=2)

                #
                ax2 = subplot(2,1,2)
                f = frame[k].f
                mask = ((f)>0.02) & ((f)<0.06)
                kind = 'psi4'
                #smoothness_measure = abs( std( frame[k][2,2][kind].fd_dphi[mask]-smooth(frame[k][2,2][kind].fd_dphi[mask]).answer ) )
                if True: #smoothness_measure[k]<10:
                    plot( f, frame[k][2,2][kind].fd_dphi-D0, label=k, alpha=1 if is_best else 0.2, ls=ls if not is_best else '-', lw=lw if not is_best else 2, color=ln[0].get_color() )
                    xlabel('$fM$')
                    xlim( 0.02, 0.11 )
                    ya,yb = lim( frame[k][2,2][kind].fd_dphi[mask]-D0 )
                    y0 = max( ya,y0 )
                    y1 = min( yb,y1 )
                    b = 0.25*abs(y1-y0)
                    ylim( y0-b,y1+b )
                #
                legend(ncol=2)
                xlabel('$fM$')
                ylabel(r'$\frac{d}{df}\arg(\tilde{\psi}_4)$')


        #
        subplot(2,1,1)
        title(y_raw.simname)
        
        #
        return fig,[ax1,ax2]
        
    #
    fig,ax = plot_amp_dphi(frame)
    file_path = data_dir+'%s.png'%frame['raw'].simname
    alert('Saving diagnostic plot to "%s"'%yellow(file_path))
    savefig( file_path )
    
    # Select and output amplitude and phase data
    f = frame['raw'].f
    mask = (f>0.03) & (f<0.12) 
    
    fd_amp  = frame['star-sym-cp-y-fd'][2,2]['strain'].fd_amp
    fd_dphi = frame['star-sym-cp-y-fd'][2,2]['psi4'].fd_dphi
    fd_phi = frame['star-sym-cp-y-fd'][2,2]['psi4'].fd_phi
    #
    shift = min(smooth(fd_dphi[mask]).answer)
    fd_dphi -= shift
    fd_phi  -= f * shift
    fd_phi -= fd_phi[ sum(f<0.03)-1+argmin(smooth(fd_dphi[mask]).answer) ]
    
    td_amp  = frame['star-sym-cp-y-td'][2,2]['strain'].fd_amp
    td_dphi = frame['star-sym-cp-y-td'][2,2]['psi4'].fd_dphi
    td_phi = frame['star-sym-cp-y-td'][2,2]['psi4'].fd_phi
    #
    shift = min(smooth(td_dphi[mask]).answer)
    td_dphi -= shift
    td_phi  -= f * shift
    td_phi -= td_phi[ sum(f<0.03)-1+argmin(smooth(td_dphi[mask]).answer) ]
    
    data_array = array([ f, td_amp, fd_amp, td_dphi, fd_dphi, td_phi, fd_phi ]).T

    #
    alert('Saving waveform data to "%s"'%yellow(txt_file_path))
    # pickle.dump( data_array, open( file_path, "wb" ) )
    savetxt( txt_file_path, data_array, header='[ f, td_amp, fd_amp, td_dphi, fd_dphi, td_phi, fd_phi ], here td and fd refer to the frame type used; frequencies are positive, waveform info are symmetrized in the psi4 TD/FD coprecessing frame from NR simulation at %s'%frame['raw'].simdir )
    
alert('All done.')