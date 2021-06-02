import numpy as np
from matplotlib import pyplot as plt



#####################################################################
# Functions

def haversine( lon1, lat1, lon2, lat2 ):
    '''
    Haversine function calcculates the distance (in meters) between two points given the longitude and latitude coordiantes
    of the points. This function will also work if one of the "points" is a higher-dimensional data structure (e.g., numpy 
    array, xarray DataArray, etc...)
        lon1: longitude [degrees] of point 1
        lon1: latitude [degrees] of point 1
        lon2: longitude [degrees] of point/array 2
        lon1: latitude [degrees] of point/array 2        
    '''
    lon1 = lon1 * np.pi / 180.
    lat1 = lat1 * np.pi / 180.
    lon2 = lon2 * np.pi / 180.
    lat2 = lat2 * np.pi / 180.
    r = 6.371e6    #[m], radius of earth's curvature
    d = 2. * r * np.arcsin( np.sin( (lat2 - lat1)/2)**2. + \
                           np.cos(lat1) * np.cos(lat2) * np.sin( (lon2 - lon1)/2.)**2. )
    return d


def integrated_shear( z1D, wspd1D):
    dz_tot = z1D[-1] - z1D[0]
    BS = 0
    for i in range(1,len(z1D)):
        BS += (wspd1D[i] - wspd1D[i-1]) / (z1D[i] - z1D[i-1])
    BS = BS * dz_tot
    
    return BS

def bulk_shear( z1D, wspd1D):
    BS = ( wspd1D[-1] - wspd1D[0] ) / ( z1D[-1] - z1D[0] )
    return BS


#####################################################################
# Plotting functions

def plot_singletime_v_prof_h_avg( ds_WRF, ds_OBS, tt, i, j, \
                                 plot_objs = None, \
                                 save_str = None, \
                                 wrf_lab = 'WRF-LES', \
                                 ncell_avg = 5 ):
    '''
    Function accepts a WRF xarray DataSeries, an OBS xarray DataSeries, a datetime object,
    and horizontal indices and uses this to average over the spatial dimension. Overlays model and observatios
    
    The function returns the plotting objects (f, ax), and can accept a plotting object to overlay additional model runs on.
    
        ds_WRF: xarray dataseries (the main code gives this function a 10-min resample of the xarray, \
                this could get slow with the full raw WRF output)
        ds_OBS: xarray dataserues as read using open_mfdataset.
        tt: datetime object to select when in the time series is plotted
                -The way that the time selecting is done is pretty convoluted and inefficient, probably could be easily improved
        i, j: horizontal indices to grab from the WRF output
        plot_objs: tuple containing (f, ax) where f is the plot figure and ax is the axis object. If these arguments are not
                provided, they will be generated by the function, only provide this argument if you want to overlay 
                on an existing plot
        save_str: (str) file path/name to save figure to (default is None)
        wrf_lab: Legend entry for the WRF simulation being plotted
        ncell_avg: number of x and y (i and j) grid cells averaged together to produce the vertical profile.
    '''
        
    tind_data = np.where( ds_OBS.datetime == tt )[0][0]
    wspd_obs = ds_OBS.isel(datetime = tind_data ).wspd.values
    levels_obs = ds_OBS.spd_levels.values
    
    tind_wrf = np.where( ds_WRF.datetime == tt )[0][0]
    
    i_ub = i[0] + ncell_avg
    i_lb = i[0] - ncell_avg
    
    j_ub = j[0] + ncell_avg
    j_lb = j[0] - ncell_avg
    
    
    
    wspd_wrf = ds_WRF.isel(nx = slice( j_lb , j_ub ) , \
                           ny = slice( i_lb , i_ub ) ,\
                           datetime = tind_wrf ).wspd.mean(dim = ('nx', 'ny') ) 
    
    try:
        f, ax = plot_objs
        ax.plot( wspd_wrf, ds_WRF.z1D.isel( datetime = tind_wrf ), 'k--', label = wrf_lab)
        ax.legend(loc = 'best')
    except:
        f, ax = plt.subplots(figsize = (7,5))
        ax.plot( wspd_wrf, ds_WRF.z1D.isel(datetime = tind_wrf), 'k', label = wrf_lab)
        ax.scatter( ds_OBS.isel(datetime = tind_data ).wspd, ds_OBS.spd_levels,s = 50, marker = 'x', label = 'FINO 1 data')

        ax.set_xlabel('Windspeed [m/s]')
        ax.set_ylabel('H [m]')

        ax.set_ylim([0., 110])
        ax.set_xlim([0., 18.])

        

        ax.set_title(tt.values)#.strftime('%YYYY-%m-%d %HH:%MM:%SS'))
    
    try:
        print(save_str)
        plt.savefig( save_str, dpi = 300 )
    except:
        print('no save string provided')
    
    return f, ax



def plot_timecolor_v_prof_h_avg( ds_WRF=None, ds_OBS=None, i = 100, j = 100, \
                                 vname = 'wspd', \
                                 obs_vc = 'spd_levels', \
                                 save_str = None, \
                                 wrf_lab = 'WRF-LES', \
                                 ncell_avg = 5 ):                                 
    try:
        NTwrf = len(ds_WRF.datetime)
        print("ds_WRF suppled, doing model profiles")
        do_wrf = True
    except:
        print("No WRF dataseries provided")
        do_wrf = False
    try:
        NTobs = len(ds_OBS.datetime)
        print("ds_OBS suppled, doing data profiles")
        do_obs = True
    except:
        print("No OBS dataseries provided")
        do_obs = False
    if not do_wrf:
        if not do_obs:
            print("No DataSeries provided, what are you doing?")
            print("Must provide at lesat one ds_WRF or ds_OBS as argument")
            print("Exiting")
            return

    NT = NTwrf
    times = ds_WRF.datetime

    # Set colormap
    
    cmap = plt.cm.viridis( np.linspace( 0, 1, int(NT) ))
    
    
    i_ub = i[0] + ncell_avg
    i_lb = i[0] - ncell_avg
    
    j_ub = j[0] + ncell_avg
    j_lb = j[0] - ncell_avg
    
    try:
        f, ax = plot_objs
        plot_objs_args = True
    except:
        f, ax = plt.subplots()
        plot_objs_args = False
    ct = 0
    
    for tt in times:
        
        if do_wrf:
            try:
                tind_wrf = np.where(ds_WRF.datetime == tt )[0][0]
            
                temp_var = ds_WRF[vname].isel(nx = slice(j_lb, j_ub), \
                                         ny = slice(i_lb, i_ub), \
                                         datetime = slice(tind_wrf, int(tind_wrf+6)) ).mean( dim = ('datetime','nx', 'ny') ) 

            
            

                ax.plot( temp_var, ds_WRF.z1D.isel(datetime = tind_wrf), color = cmap[ct] )
            except:
                print("WRF output missing this time")
        if do_obs:
            try:
                tind_OBS = np.where(ds_OBS.datetime == tt )[0]
                
                ax.scatter( ds_OBS[vname].isel(datetime = tind_OBS), ds_OBS[obs_vc], color = cmap[ct] )
            except:
                print("OBS output missing this time")
        
        ct += 1
    if not plot_objs_args:
        ax.set_title(wrf_lab)
        ax.set_xlabel(vname)
        ax.set_ylabel('Height [m]' )

    try:
        plt.savefig( save_str, dpi = 300 )
        print( "Saving" )
    except:
        print( "Not saving, save_str not provided" )
        
        
    return (f,ax)
                                
                                


def plot_timecolor_v_prof_diff_h_avg( ds_WRF1, ds_WRF2, \
                                      i = 100, j = 100, \
                                      vname = 'wspd', \
                                      save_str = None, \
                                      wrf_lab = 'WRF-LES', \
                                      ncell_avg = 5 ):                                 
    NT = len(ds_WRF1.datetime)
    cmap = plt.cm.viridis( np.linspace( 0, 1, NT ))
    
    
    i_ub = i[0] + ncell_avg
    i_lb = i[0] - ncell_avg
    
    j_ub = j[0] + ncell_avg
    j_lb = j[0] - ncell_avg
    
    try:
        f, ax = plot_objs
        plot_objs_args = True
    except:
        f, ax = plt.subplots()
        plot_objs_args = False
    ct = 0
    for tt in ds_WRF1.datetime:
       
        #try:
        tind_wrf = np.where(ds_WRF1.datetime == tt )[0][0]
        
        temp_var = ds_WRF1[vname].isel(nx = slice(j_lb, j_ub), \
                  ny = slice(i_lb, i_ub), \
                  datetime = tind_wrf)  - \
                  ds_WRF2[vname].isel(nx = slice(j_lb, j_ub), \
                  ny = slice(i_lb, i_ub), \
                  datetime = tind_wrf)

        ax.plot(  temp_var.mean(dim = ('nx', 'ny')), \
                  ds_WRF1.z1D.isel(datetime = tind_wrf), c = cmap[ct] )
        #except:
        #    print("WRF output missing this time")
        ct += 1
    if not plot_objs_args:
        ax.set_title(wrf_lab)
        ax.set_xlabel('Windspeed Difference [m/s]')
        ax.set_ylabel('Height [m]' )

    try:
        plt.savefig( save_str, dpi = 300 )
        print( "Saving" )
    except:
        print( "Not saving, save_str not provided" )
        
        
    return (f,ax)




def plan_view_pcolor( ds, \
                     vname = 'wspd', \
                     cblabel = 'WSPD [m/s]', \
                     zlev_ind = 22, time_ind = 40, \
                     cb_vmin = 10, cb_vmax = 18, clabel = 'WSPD [m/s]',\
                     scatter_x_arr = None, scatter_y_arr = None, \
                     scatter_x_sp = None, scatter_y_sp = None, \
                     plot_obj = None ):
    
    var_inst = ds[vname].isel(nz = zlev_ind, datetime = time_ind )
    z_inst = ds.z.isel(nz = zlev_ind, datetime = time_ind ).mean(['nx','ny']).values
    
    print(z_inst)
    if not plot_obj:
        f, ax  = plt.subplots( figsize = (10,10))
    else:
        f, ax = plot_obj
    pc = ax.pcolor( ds.x, ds.y, var_inst, vmin=cb_vmin, vmax = cb_vmax )
    
    if scatter_x_arr:
        ax.scatter( ds.x.isel( nx = scatter_x_arr ) , ds.y.isel( ny = scatter_y_arr ), color = 'black')
        
    if scatter_x_sp:
        ax.scatter( ds.x.isel( nx = scatter_x_sp ) , ds.y.isel( ny = scatter_y_sp ), color = 'red')


    if not plot_obj:
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        f.colorbar( pc, label = clabel )
        ax.set_title(f'Z {z_inst} m AGL')
    
    return f, ax, pc

def plot_spacecolor_v_prof_h_avg( ds_WRF,                                       
                                  i_arr, j_arr, \
                                  ti0 = 0, tiF = 6,
                                  vname = 'wspd', \
                                  save_str = None, \
                                  wrf_lab = 'WRF-LES', \
                                  ncell_avg = 5 ):                                  

    NT = len(i_arr)
    cmap = plt.cm.viridis( np.linspace( 0, 1, NT ))
    
    

    
    try:
        f, ax = plot_objs
        plot_objs_args = True
    except:
        f, ax = plt.subplots()
        plot_objs_args = False
    ct = 0
    for ii in range(0,NT):
        i_ub = i_arr[ii] + ncell_avg
        i_lb = i_arr[ii] - ncell_avg
    
        j_ub = j_arr[ii] + ncell_avg
        j_lb = j_arr[ii] - ncell_avg
       
        #try:
        #tind_wrf = np.where(ds_WRF1.datetime == tt )[0][0]
        
        temp_var = ds_WRF[vname].isel(nx = slice(j_lb, j_ub), \
                  ny = slice(i_lb, i_ub), \
                  datetime = slice(ti0,tiF) )

        ax.plot(  temp_var.mean(dim = ('nx', 'ny', 'datetime')), \
                  ds_WRF.z1D.isel(datetime = slice(ti0,tiF)).mean('datetime'), c = cmap[ct] )
        #except:
        #    print("WRF output missing this time")
        ct += 1
    if not plot_objs_args:
        ax.set_title(wrf_lab)
        ax.set_xlabel('Windspeed Difference [m/s]')
        ax.set_ylabel('Height [m]' )

    try:
        plt.savefig( save_str, dpi = 300 )
        print( "Saving" )
    except:
        print( "Not saving, save_str not provided" )
        
        
    return (f,ax)


def plot_spacecolor_v_prof_diff_h_avg( ds_WRF1, ds_WRF2, \
                                      i_arr, j_arr, \
                                      ti0 = 0, tiF = 6,
                                      vname = 'wspd', \
                                      save_str = None, \
                                      wrf_lab = 'WRF-LES', \
                                      ncell_avg = 5 ):  
    NT = len(i_arr)
    cmap = plt.cm.viridis( np.linspace( 0, 1, NT ))
    
    

    
    try:
        f, ax = plot_objs
        plot_objs_args = True
    except:
        f, ax = plt.subplots()
        plot_objs_args = False
    ct = 0
    for ii in range(0,NT):
        i_ub = i_arr[ii] + ncell_avg
        i_lb = i_arr[ii] - ncell_avg
    
        j_ub = j_arr[ii] + ncell_avg
        j_lb = j_arr[ii] - ncell_avg
       
        #try:
        #tind_wrf = np.where(ds_WRF1.datetime == tt )[0][0]
        
        temp_var = ds_WRF1[vname].isel(nx = slice(j_lb, j_ub), \
                  ny = slice(i_lb, i_ub), \
                  datetime = slice(ti0,tiF))  - \
                  ds_WRF2[vname].isel(nx = slice(j_lb, j_ub), \
                  ny = slice(i_lb, i_ub), \
                  datetime = slice(ti0,tiF))

        ax.plot(  temp_var.mean(dim = ('nx', 'ny', 'datetime')), \
                  ds_WRF1.z1D.isel(datetime=slice(ti0,tiF)).mean('datetime'), c = cmap[ct] )
        #except:
        #    print("WRF output missing this time")
        ct += 1
    if not plot_objs_args:
        ax.set_title(wrf_lab)
        ax.set_xlabel('Windspeed Difference [m/s]')
        ax.set_ylabel('Height [m]' )

    try:
        plt.savefig( save_str, dpi = 300 )
        print( "Saving" )
    except:
        print( "Not saving, save_str not provided" )
        
        
    return (f,ax)