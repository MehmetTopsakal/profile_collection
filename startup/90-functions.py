print(f'Loading {__file__}')



def configure_area_det(det,acq_time,acq_period=None,exposure=None,num_exposures=1):
    """
    Used to configure detectors at 28ID-2-tomo endstation.
    Averaging through proc plugin is used.
    """
    
    
    #turn on det if it is stopped
    if det.cam.acquire.get() == 0:
        yield from bps.mov(det.cam.acquire, 1)
        
    # this cannot be less than 1    
    num_exposures = int(max(num_exposures,1))
     
    #set minimums for acq_time
    if det.name == 'dexela': 
        acq_time = max(0.1,acq_time)
    elif det.name == 'emergent':
        acq_time = max(1,acq_time)
    elif det.name == 'blackfly':
        acq_time = max(0.1,acq_time)        
    elif det.name == 'prosilica':
        acq_time = max(0.1,acq_time)   
        
    #set minimums for acq_period (not used for some of dets)        
    if acq_period is None:
        if det.name == 'blackfly':
            acq_period = min(0.1,acq_time)
        elif det.name == 'dexela':
            acq_period = acq_time+0.01
        else:
            acq_period = acq_time
    else:
        acq_period = min(acq_period,acq_time)
        
    if exposure is None:
        exposure = acq_time*10  
        

    num_frames = np.ceil(exposure / acq_time)  
    

    yield from bps.mov(det.cam.acquire_time, acq_time, 
                       det.cam.acquire_period, acq_period, 
                       det.images_per_set, num_frames, 
                       det.number_of_sets, num_exposures
                      )

    if det.name == 'emergent': 
        print(">>>%s is configured as:\n acq_time = %.3fmsec;  acq_period = %.3fmsec; exposure = %.3fmsec \
    (num frames = %.2f); num_exposures = %d"%(det.name,det.cam.acquire_time.get(),det.cam.acquire_period.get(),exposure,num_frames,num_exposures))
    else:
        print(">>>%s is configured as:\n acq_time = %.3fmsec;  acq_period = %.3fsec; exposure = %.3fmsec \
    (num frames = %.2f); num_exposures = %d"%(det.name,det.cam.acquire_time.get(),det.cam.acquire_period.get(),exposure,num_frames,num_exposures))
    

    return













def md_getter():

    import time

    md = {}

    md['time'] = time.time()

    md['md_time'] = time.strftime('%Y/%m/%d - %H:%M:%S')


    for f in [Filters.flt1,Filters.flt2,Filters.flt3,Filters.flt4]:
        md[f.name] = f.get()    


    for m in [FastShutter,
              mTopX, 
              mTopY, 
              mTopZ, 
              mPhi,
              ePhi,
              mRoll, 
              mPitch,
              mBaseX,
              mBaseY,
              mDexelaPhi,
              mQuestarX,
              mBeamStopY,
              mHexapodsZ,
              mSlitsYGap,    
              mSlitsYCtr,    
              mSlitsXGap,    
              mSlitsXCtr,    
              mSlitsTop,     
              mSlitsBottom,  
              mSlitsOutboard,
              mSlitsInboard, 
              mSigrayX,    
              mSigrayY,    
              mSigrayZ,    
              mSigrayPitch,
              mSigrayYaw,
             ]:
            md[m.name] = float('%.4f'%m.position)

    sSmartPodUnit.set(0)
    time.sleep(0.2)
    sSmartPodSync.set(1)
    time.sleep(0.2)
    for s in [
             sSmartPodUnit, 
             sSmartPodTrasZ,
             sSmartPodTrasX,
             sSmartPodTrasY,
             sSmartPodRotZ, 
             sSmartPodRotX, 
             sSmartPodRotY, 
             sSmartPodSync, 
             sSmartPodMove, 
             ]:
            md['%s_0'%s.name] = float('%.5f'%s.get())            

    sSmartPodUnit.set(1)
    time.sleep(0.2)
    sSmartPodSync.set(1)
    time.sleep(0.2)
    for s in [
             sSmartPodUnit, 
             sSmartPodTrasZ,
             sSmartPodTrasX,
             sSmartPodTrasY,
             sSmartPodRotZ, 
             sSmartPodRotX, 
             sSmartPodRotY, 
             sSmartPodSync, 
             sSmartPodMove, 
             ]:
            md['%s_1'%s.name] = float('%.5f'%s.get())    

    for s in [
             pdu1,pdu2,pdu3,pdu4,ring_current 
             ]:
            md[s.name] = float('%.2f'%s.get())  

    return md








def beam_on(shutter_motor=None,sleep=0.1):
    if shutter_motor is None:
        shutter_motor =  FastShutter
    shutter_motor.move(0,wait=True)
    time.sleep(sleep)

def beam_off(shutter_motor=None,sleep=0.1):
    if shutter_motor is None:
        shutter_motor =  FastShutter
    shutter_motor.move(-47,wait=True)
    time.sleep(sleep)




def pud_switcher(ipdu, state='off', verbose=False):

    pdus = (pdu1,pdu2,pdu3,pdu4)

    if state == 'on' or state == 1:
        current_state = pdus[ipdu].get()
        if current_state == 1:
            if verbose:
                print('it is already on!')
        else:
            pdus[ipdu].set(1)
            time.sleep(0.1)

    if state == 'off' or state == 0:
        current_state = pdus[ipdu].get()
        if current_state == 0:
            if verbose:
                print('it is already off!')
        else:
            pdus[ipdu].set(0)
            time.sleep(0.1)






def read_tiff_as_xarray(tiffpath,
                       figsize=(6,6),
                       robust=True,
                       plot=False,
                       cbar=False,
                       mode=None):

    """
    Reads a tiff file as xarray
    """

    if mode == 'prosilica':
        img = fabio.open(tiffpath).data
    else:
        img = tifffile.imread(tiffpath).astype('float32')

    da = xr.DataArray(data=img,
                      coords=[np.arange(img.shape[0]),np.arange(img.shape[1])],
                      dims=['pixel_y', 'pixel_x'])

    if plot:

        fig = plt.figure(figsize=figsize)

        ax = fig.add_subplot(1,1,1)

        if not cbar:
            xp = da.plot.imshow(ax=ax,robust=robust,
                                yincrease=False,
                                cmap='Greys_r',
                                add_colorbar=cbar)
        else:
            xp = da.plot.imshow(ax=ax,robust=robust,
                                yincrease=False,
                                cmap='Greys_r',
                                cbar_kwargs=dict(orientation='vertical',
                                            pad=0.07, 
                                            shrink=0.4, 
                                            label='Intensity'))            

        xp.axes.set_aspect('equal', 'box')

        plt.tight_layout()


    return da



def print_det_keys(det_class):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(det_class.tiff.__dict__)







def counter_1det(det=None,
                 acq_time=0.1,exposure=1,
                 include_dark=False,
                 include_flat=False,flat_motor=None,flat_motor_move=2.5,
                 ):

    if include_dark:
        beam_off()
        print('\nINFO: Taking dark\n') 
        RE(configure_area_det(det,acq_time=acq_time,exposure=exposure))
        uid_dark = RE(count([det]),md={'task':'count-dark','acq_time':acq_time,'exposure':exposure})[0]
    else:
        uid_dark = 'none'

    if include_flat:
        print('\nINFO: Taking flat\n') 
        motor_current = flat_motor.position        
        flat_motor.move(motor_current+flat_motor_move,wait=True)
        print([motor_current,flat_motor.position])
        beam_on()
        RE(configure_area_det(det,acq_time=acq_time,exposure=exposure))
        uid_flat = RE(count([det]),md={'task':'count-flat',
                                       'acq_time':acq_time,
                                       'exposure':exposure,
                                       'flat_motor':flat_motor.name,
                                       'flat_motor_move':flat_motor_move})[0]
        beam_off()
        flat_motor.move(motor_current,wait=True) 
    else:
        uid_flat = 'none'

    beam_on()
    RE(configure_area_det(det,acq_time=acq_time,exposure=exposure)) 
    uid_light = RE(count([det]),md={'task':'count-light',
                                    'acq_time':acq_time,
                                    'exposure':exposure})[0]
    beam_off()

    return uid_light, uid_flat, uid_dark


def linescanner_1det(
                    det = None,
                    det_acq_time = 4,

                    include_dark = False,
                    det_exposure_dark = 4,    

                    include_flat=False,
                    flat_motor=None,
                    flat_motor_move=2.5,

                    det_exposure_linescan = 4,
                    motor = None,
                    motor_start = None,
                    motor_stop  = None,
                    motor_nstep = 11,

                    come_back = True,

                    ):

    if include_dark:
        beam_off()
        print('\n>>>> Taking dark\n') 
        RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_dark))
        uid_dark = RE(count([det]),md={'task':'dark','acq_time':det_acq_time,'exposure':det_exposure_dark})[0]
    else:
        uid_dark = 'none'

    if include_flat:
        print('\nINFO: Taking flat\n') 
        motor_current = flat_motor.position        
        flat_motor.move(motor_current+flat_motor_move,wait=True)
        print([motor_current,flat_motor.position])
        beam_on()
        RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_dark))
        uid_flat = RE(count([det]),md={'task':'linescan-flat',
                                       'acq_time':det_acq_time,
                                       'exposure':det_exposure_dark,
                                       'flat_motor':flat_motor.name,
                                       'flat_motor_move':flat_motor_move})[0]
        beam_off()
        flat_motor.move(motor_current,wait=True) 
    else:
        uid_flat = 'none'        

    motor_current_pos = motor.position
    print('>>> %s @ %.3f'%(motor.name,motor_current_pos))

    RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_linescan))
    beam_on()
    uid_linescan = RE(scan([det],motor,motor_start,motor_stop,motor_nstep),md={'task':'linescan','acq_time':det_acq_time,'exposure':det_exposure_linescan})[0]
    beam_off()

    if come_back:
        print('>>> Moving %s back to %.3f'%(motor.name,motor_current_pos))
        motor.move(motor_current_pos)

    return uid_linescan, uid_flat, uid_dark















def gridscanner_1det(    
                    det = None,
                    det_acq_time = 2,
                    include_dark = True,
                    det_exposure_dark = 2,
                    det_exposure_gridscan = 2,

                    include_flat=False,
                    flat_motor=None,
                    flat_motor_move=None,    

                    #put slowest motor first
                    motor1 = None,
                    motor1_start = None,
                    motor1_stop  = None,
                    motor1_nstep = None,

                    motor2 = None,
                    motor2_start = None,
                    motor2_stop  = None,
                    motor2_nstep = None,

                    snake=True,
                    come_back = True,

                    ):


    if include_dark:
        print('\n>>>> Taking dark\n') 
        beam_off()
        RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_dark))
        uid_dark = RE(count([det]),md={'task':'dark','acq_time':det_acq_time,'exposure':det_exposure_dark})[0]
    else:
        uid_dark = 'none'

    if include_flat:
        print('\nINFO: Taking flat\n') 
        motor_current = flat_motor.position        
        flat_motor.move(motor_current+flat_motor_move,wait=True)
        print([motor_current,flat_motor.position])
        beam_on()
        RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_dark))
        uid_flat = RE(count([det]),md={'task':'linescan-flat',
                                       'acq_time':det_acq_time,
                                       'exposure':det_exposure_dark,
                                       'flat_motor':flat_motor.name,
                                       'flat_motor_move':flat_motor_move})[0]
        beam_off()
        flat_motor.move(motor_current,wait=True) 
    else:
        uid_flat = 'none' 

    motor1_current_pos = motor1.position
    print('>>> %s @ %.3f'%(motor1.name,motor1_current_pos))
    motor2_current_pos = motor2.position
    print('>>> %s @ %.3f'%(motor2.name,motor2_current_pos))

    beam_on()
    RE(configure_area_det(det,acq_time=det_acq_time,exposure=det_exposure_gridscan))

    uid_gridscan = RE(grid_scan([det],
                                motor1,motor1_start,motor1_stop,motor1_nstep,
                                motor2,motor2_start,motor2_stop,motor2_nstep,
                                snake_axes=snake),
                                md={'task':'gridscan','acq_time':det_acq_time,'exposure':det_exposure_gridscan})[0]
    beam_off()

    if come_back:
        print('>>> Moving %s back to %.3f'%(motor1.name,motor1_current_pos))
        motor1.move(motor1_current_pos)
        print('>>> Moving %s back to %.3f'%(motor2.name,motor2_current_pos))
        motor2.move(motor2_current_pos)    

    return uid_gridscan, uid_flat, uid_dark    

























def ds_maker(js,return_ds=False,run_md_getter=True,dtype=None):


################################################################################################################ 
########################################## count_1det ########################################################## 
################################################################################################################    
    if js['task'] == 'count_1det':  

        ds = xr.Dataset()

        if js['uid_dark'] != 'none':
            ds_dark = raw[js['uid_dark']].primary.read()
            hdr_dark = db[js['uid_dark']]
            md_dark = hdr_dark.start['md']
            da_dark = xr.DataArray(data=ds_dark['%s_image'%hdr_dark.start['detectors'][0]].squeeze(('time','dim_0')).values,
                  coords=[ds_dark.dim_1, ds_dark.dim_2],
                  dims=['%s_pixel_y'%(hdr_dark.start['detectors'][0]), '%s_pixel_x'%(hdr_dark.start['detectors'][0])],
                  attrs={'uid':js['uid_dark'],
                         'acq_time':md_dark['acq_time'],
                         'exposure':md_dark['exposure'],
                        }
                 )
            if dtype is None:
                ds['dark'] = da_dark
            else:
                ds['dark'] = da_dark.astype(dtype,copy=False)

        if js['uid_flat'] != 'none':
            ds_flat = raw[js['uid_flat']].primary.read()
            hdr_flat = db[js['uid_flat']]
            md_flat = hdr_flat.start['md']
            try:
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure'],
                             'flat_motor':md_flat['flat_motor'],
                             'flat_motor_move':md_flat['flat_motor_move'],
                            }
                     )
            except:
                print('uid_flat does not contain motor information')
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure']
                            }
                     )                
            if dtype is None:
                ds['flat'] = da_flat
            else:
                ds['flat'] = da_flat.astype(dtype,copy=False)

        ds_light = raw[js['uid_light']].primary.read()
        hdr_light = db[js['uid_light']]
        md_light = hdr_light.start['md']
        da_light = xr.DataArray(data=ds_light['%s_image'%hdr_light.start['detectors'][0]].squeeze(('time','dim_0')).values,
              coords=[ds_light.dim_1, ds_light.dim_2],
              dims=['%s_pixel_y'%(hdr_light.start['detectors'][0]), '%s_pixel_x'%(hdr_light.start['detectors'][0])],
              attrs={'uid':js['uid_light'],
                     'acq_time':md_light['acq_time'],
                     'exposure':md_light['exposure'],
                    }
             )
        if dtype is None:
            ds['light'] = da_light
        else:
            ds['light'] = da_light.astype(dtype,copy=False)

        if run_md_getter:
            z = ds.attrs.copy()
            z.update(md_getter())
            ds.attrs = z        

        comp = dict(zlib=False)
        encoding = {var: comp for var in ds.data_vars}
        ds.to_netcdf(js['nc_path'], encoding=encoding)  

        if return_ds:
            print(js['nc_path'])
            return ds
        else:
            return js['nc_path']   






################################################################################################################ 
########################################## linescan_1det ####################################################### 
################################################################################################################      
    if js['task'] == 'linescan_1det': 

        ds = xr.Dataset()

        ds_linescan = raw[js['uid_linescan']].primary.read()
        hdr_linescan = db[js['uid_linescan']]
        md_linescan = hdr_linescan.start['md']
        da_linescan = xr.DataArray(data=ds_linescan['%s_image'%hdr_linescan.start['detectors'][0]].squeeze('dim_0').values,
                  coords=[ds_linescan['%s'%hdr_linescan.start['motors'][0]], ds_linescan.dim_1, ds_linescan.dim_2],
                  dims=['%s'%(hdr_linescan.start['motors'][0]),'%s_pixel_y'%(hdr_linescan.start['detectors'][0]), '%s_pixel_x'%(hdr_linescan.start['detectors'][0])],
                  attrs={'uid':js['uid_linescan'],
                         'acq_time':md_linescan['acq_time'],
                         'exposure':md_linescan['exposure'],
                        }
                 )
        if dtype is None:
            ds['linescan'] = da_linescan
        else:
            ds['linescan'] = da_linescan.astype(dtype,copy=False)

        da_stats1_total = xr.DataArray(data=ds_linescan['%s_stats1_total'%hdr_linescan.start['detectors'][0]].values,
                  coords=[ds_linescan['%s'%hdr_linescan.start['motors'][0]]],
                  dims=[hdr_linescan.start['motors'][0]],
                 )
        ds['stats1_total'] = da_stats1_total

        ds = ds.assign_coords(time = ds_linescan.time)


        if js['uid_dark'] != 'none':
            ds_dark = raw[js['uid_dark']].primary.read()
            hdr_dark = db[js['uid_dark']]
            md_dark = hdr_dark.start['md']
            da_dark = xr.DataArray(data=ds_dark['%s_image'%hdr_dark.start['detectors'][0]].squeeze(('time','dim_0')).values,
                  coords=[ds_dark.dim_1, ds_dark.dim_2],
                  dims=['%s_pixel_y'%(hdr_dark.start['detectors'][0]), '%s_pixel_x'%(hdr_dark.start['detectors'][0])],
                  attrs={'uid':js['uid_dark'],
                         'acq_time':md_dark['acq_time'],
                         'exposure':md_dark['exposure'],
                        }
                 )
            if dtype is None:
                ds['dark'] = da_dark
            else:
                ds['dark'] = da_dark.astype(dtype,copy=False) 


        if js['uid_flat'] != 'none':
            ds_flat = raw[js['uid_flat']].primary.read()
            hdr_flat = db[js['uid_flat']]
            md_flat = hdr_flat.start['md']
            try:
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure'],
                             'flat_motor':md_flat['flat_motor'],
                             'flat_motor_move':md_flat['flat_motor_move'],
                            }
                     )
            except:
                print('uid_flat does not contain motor information')
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure']
                            }
                     )                
            if dtype is None:
                ds['flat'] = da_flat
            else:
                ds['flat'] = da_flat.astype(dtype,copy=False)           

        if run_md_getter:
            z = ds.attrs.copy()
            z.update(md_getter())
            ds.attrs = z        

        comp = dict(zlib=False)
        encoding = {var: comp for var in ds.data_vars}
        ds.to_netcdf(js['nc_path'], encoding=encoding)


        if return_ds:
            print(js['nc_path'])
            return ds
        else:
            return js['nc_path']      






################################################################################################################ 
########################################## gridscan_1det_2motors ############################################### 
################################################################################################################      

    if js['task'] == 'gridscan_1det_2motors': 

        ds = xr.Dataset()

        ds_gridscan = raw[js['uid_gridscan']].primary.read()
        hdr_gridscan = db[js['uid_gridscan']]
        md_gridscan = hdr_gridscan.start['md']

        if hdr_gridscan['start']['snaking'][1]:

            data_ds = ds_gridscan['%s_image'%hdr_gridscan.start['detectors'][0]].squeeze('dim_0').values
            data = np.zeros(((hdr_gridscan['start']['shape'][0],
                              hdr_gridscan['start']['shape'][1],
                              ds_gridscan.dim_1.shape[0],
                              ds_gridscan.dim_2.shape[0],
                             )))
            c = 0
            s = 0
            for i in range(hdr_gridscan['start']['shape'][0]):        
                if s == 0:
                    for j in range(hdr_gridscan['start']['shape'][1]):
                        data[i,j,:,:] = data_ds[c,:,:]
                        c += 1
                    s = 1
                else:
                    for j in range(hdr_gridscan['start']['shape'][1]):
                        data[i,j-hdr_gridscan['start']['shape'][1]+1,:,:] = data_ds[c,:,:]
                        c += 1
                    s = 0

        else:    
            data_ds = ds_gridscan['%s_image'%hdr_gridscan.start['detectors'][0]].squeeze('dim_0').values

            data = np.zeros(((hdr_gridscan['start']['shape'][0],
                              hdr_gridscan['start']['shape'][1],
                              ds_gridscan.dim_1.shape[0],
                              ds_gridscan.dim_2.shape[0],
                             )))

            c = 0
            for i in range(hdr_gridscan['start']['shape'][0]):
                for j in range(hdr_gridscan['start']['shape'][1]):
                    data[i,j,:,:] = data_ds[c,:,:]
                    c += 1


        da_gridscan = xr.DataArray(data=data,

                  coords=[
                        np.linspace(hdr_gridscan['start']['extents'][0][0],
                                    hdr_gridscan['start']['extents'][0][1],
                                    hdr_gridscan['start']['shape'][0]),
                        np.linspace(hdr_gridscan['start']['extents'][1][0],
                                    hdr_gridscan['start']['extents'][1][1],
                                    hdr_gridscan['start']['shape'][1]),
                          ds_gridscan.dim_1,
                          ds_gridscan.dim_2],

                  dims=[
                      '%s'%hdr_gridscan.start['motors'][0],
                        '%s'%hdr_gridscan.start['motors'][1],
                        '%s_pixel_y'%(hdr_gridscan.start['detectors'][0]),
                        '%s_pixel_x'%(hdr_gridscan.start['detectors'][0])],

                  attrs={'uid':js['uid_gridscan'],
                         'acq_time':md_gridscan['acq_time'],
                         'exposure':md_gridscan['exposure'],
                        }
                 )
        if dtype is None:
            ds['gridscan'] = da_gridscan
        else:
            ds['gridscan'] = da_gridscan.astype(dtype,copy=False)   


        if js['uid_dark'] != 'none':
            ds_dark = raw[js['uid_dark']].primary.read()
            hdr_dark = db[js['uid_dark']]
            md_dark = hdr_dark.start['md']
            da_dark = xr.DataArray(data=ds_dark['%s_image'%hdr_dark.start['detectors'][0]].squeeze(('time','dim_0')).values,
                  coords=[ds_dark.dim_1, ds_dark.dim_2],
                  dims=['%s_pixel_y'%(hdr_dark.start['detectors'][0]), '%s_pixel_x'%(hdr_dark.start['detectors'][0])],
                  attrs={'uid':js['uid_dark'],
                         'acq_time':md_dark['acq_time'],
                         'exposure':md_dark['exposure'],
                        }
                 )
            if dtype is None:
                ds['dark'] = da_dark
            else:
                ds['dark'] = da_dark.astype(dtype,copy=False)  


        if js['uid_flat'] != 'none':
            ds_flat = raw[js['uid_flat']].primary.read()
            hdr_flat = db[js['uid_flat']]
            md_flat = hdr_flat.start['md']
            try:
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure'],
                             'flat_motor':md_flat['flat_motor'],
                             'flat_motor_move':md_flat['flat_motor_move'],
                            }
                     )
            except:
                print('uid_flat does not contain motor information')
                da_flat = xr.DataArray(data=ds_flat['%s_image'%hdr_flat.start['detectors'][0]].squeeze(('time','dim_0')).values,
                      coords=[ds_flat.dim_1, ds_flat.dim_2],
                      dims=['%s_pixel_y'%(hdr_flat.start['detectors'][0]), '%s_pixel_x'%(hdr_flat.start['detectors'][0])],
                      attrs={'uid':js['uid_flat'],
                             'acq_time':md_flat['acq_time'],
                             'exposure':md_flat['exposure']
                            }
                     )                
            if dtype is None:
                ds['flat'] = da_flat
            else:
                ds['flat'] = da_flat.astype(dtype,copy=False)             

        if run_md_getter:
            z = ds.attrs.copy()
            z.update(md_getter())
            ds.attrs = z         

        comp = dict(zlib=False)
        encoding = {var: comp for var in ds.data_vars}
        ds.to_netcdf(js['nc_path'], encoding=encoding)

        if return_ds:
            print(js['nc_path'])
            return ds
        else:
            return js['nc_path']   






import pymatgen as mg
from pymatgen.analysis.diffraction.xrd import XRDCalculator
from copy import deepcopy
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure

#from https://github.com/scikit-beam/scikit-beam/blob/master/skbeam/core/utils.py
def twotheta_to_q(two_theta, wavelength):
    two_theta = np.asarray(two_theta)
    wavelength = float(wavelength)
    pre_factor = ((4 * np.pi) / wavelength)
    return pre_factor * np.sin(two_theta / 2)
def q_to_twotheta(q, wavelength):
    q = np.asarray(q)
    wavelength = float(wavelength)
    pre_factor = wavelength / (4 * np.pi)
    return 2 * np.arcsin(q * pre_factor)

###mp_id materials project id for the sample, input
def xrd_plotter(ax=None,mp_id=None,final=False,structure=None,str_file=None,label=None,scale=1.00,
                marker='o',color='C0',label_yshift=0,label_xshift=0.1,
                bottom=-0.2,
                unit='q_A^-1', radial_range=(1,10),
                wl=0.77,
                stem=False,stem_scale='sqrt',normalize=True,yscale=1):    

    if mp_id is not None:    
        from pymatgen.ext.matproj import MPRester
        mpr = MPRester('gI8Qmxe9AnkbTvNd')  ###
        structure = mpr.get_structure_by_material_id(mp_id,final=final)  ##if there is a mp_id, assign it a structure via the materials project database
    elif structure is None:
        structure = Structure.from_file(str_file)   ###if there is no structure, it wil complain

    structure.lattice = Lattice.from_parameters(a=structure.lattice.abc[0]*scale, 
                                                b=structure.lattice.abc[1]*scale,
                                                c=structure.lattice.abc[2]*scale,
                                                alpha=structure.lattice.angles[0],
                                                beta =structure.lattice.angles[1],
                                                gamma=structure.lattice.angles[2]
                                                  )

    xrdc = XRDCalculator(wavelength=wl) ###computes xrd pattern given wavelength , debye scherrer rings, and symmetry precision

    if unit == 'q_A^-1':
        ps = xrdc.get_pattern(structure, scaled=True, two_theta_range=np.rad2deg(q_to_twotheta(radial_range,wl)))
        X,Y = twotheta_to_q(np.deg2rad(ps.x),wl), ps.y
    elif unit == '2th_deg':
        ps = xrdc.get_pattern(structure, scaled=True, two_theta_range=radial_range)
        X,Y = ps.x, ps.y
    else:
        ps = xrdc.get_pattern(structure, scaled=True, two_theta_range=radial_range)
        X,Y = ps.x, ps.y

    if normalize:
        Y = Y/max(Y)
    Y = yscale*Y

    if stem_scale == 'sqrt':
        Y = np.sqrt(Y)
    if stem_scale == 'log':
        Y = np.log(Y)       

    for i in X:
        ax.axvline(x=i,lw=0.2,color=color)

    if stem:
        ax.stem(X,Y+bottom,bottom=bottom,
                markerfmt=color+marker,basefmt=color,linefmt=color)           

    ax.axhline(y=bottom,xmin=radial_range[0]+0.1,color=color)

    ax.text(radial_range[0]+label_xshift,bottom+label_yshift,label,color=color)

    ax.axhline(y=bottom,lw=1,color=color) 





def integrator(img,ai,mask,
               flip_mask=False,
               median_filter_size=-1,

               figsize=(12,6),dpi=96,

               npt=4000,npt_azim=360,method='csr',radial_range=(1,10),unit="q_A^-1",

               jupyter_style_plot=False,robust=True,cmap="inferno",vmin=None,vmax=None,

               plot=True,show_raw=True,ylogscale=True,xlogscale=False,
               export_xy_as=None,

               mp_id=None,cif_file=None,cif_scale=1.00,
               mp_id2=None,cif_file2=None,cif_scale2=1.00,
               mp_id3=None,cif_file3=None,cif_scale3=1.00,

               export_fig_as=None):

    if flip_mask:
        mask = np.flipud(mask)

    if median_filter_size > 1:
        img = median_filter(img, size=median_filter_size)

    i1d_m = ai.integrate1d(img,npt=npt, mask=mask, method=method, 
                            unit=unit, radial_range=radial_range)
    ds = xr.Dataset()
    da_1d = xr.DataArray(data=i1d_m.intensity,
                         coords=[i1d_m.radial],
                         dims=['radial'],
                         attrs={'unit':i1d_m.unit,
                                'xlabel':i1d_m.unit.label,
                                'ylabel':r"Intensity",
                                'method':method,
                                'radial_range':radial_range}
                     ) 
    ds['i1d'] = da_1d 

    da_mask = xr.DataArray(data=mask,
                         dims=['pixel_y','pixel_x'])    
    ds['mask'] = da_mask   

    if plot:

        fig = plt.figure(figsize=figsize,dpi=dpi)

        i2d_m = ai.integrate2d(img, npt_rad=npt, npt_azim=npt_azim, mask=mask, method=method,
                                unit=unit, radial_range=radial_range)        

        ax1 = fig.add_subplot(1,2,1)
        if jupyter_style_plot:
            jupyter.display(img,ax=ax1)
            ax1.imshow(mask,alpha=0.1,cmap='Greys')
        else:
            da_img = xr.DataArray(data=img,dims=['pixel_y','pixel_x'])    
            ds['img'] = da_img
            ds['img'].plot.imshow(ax=ax1,robust=robust,cmap=cmap,vmin=vmin,vmax=vmax,
                        yincrease=False,
                        add_colorbar=True,
                        cbar_kwargs=dict(orientation='vertical',
                        pad=0.02, shrink=0.6, label=None))  
            ax1.set_aspect('equal')
            ax1.imshow(mask,alpha=0.1,cmap='Greys')

        if median_filter_size > 1:
            ax1.set_title('Median_filtered 2D image')
        else:
            ax1.set_title('2D image')

        ax2 = fig.add_subplot(2,2,2)
        if jupyter_style_plot:
            jupyter.plot2d(i2d_m,ax=ax2)
        else:
            da_2d = xr.DataArray(data=i2d_m.intensity,
                                 coords=[i2d_m.azimuthal,i2d_m.radial],
                                 dims=['azimuthal','radial'],
                                 attrs={'unit':i2d_m.unit,
                                        'xlabel':i2d_m.unit.label,
                                        'ylabel':r"Azimuthal angle $\chi$ ($^{o}$)"})              
            ds['i2d'] = da_2d 
            ds['i2d'].plot.imshow(ax=ax2,robust=robust,cmap=cmap,vmin=vmin,vmax=vmax,
                        yincrease=False,
                        add_colorbar=False)  
            ax2.set_ylabel(da_2d.attrs['ylabel'])

        ax2.set_xlim(radial_range)
        ax2.set_xlabel(None)
        ax2.set_xticklabels([])
        if median_filter_size > 1:
            ax2.set_title('Median_filtered, masked and regrouped')
        else:
            ax2.set_title('Masked and regrouped')


        ax3 = fig.add_subplot(2,2,4)

        if cif_file is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id,final=False,structure=None,
                        str_file=cif_file,label=None,scale=cif_scale,unit=unit,
                            marker='o',color='r',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9)  
            ax3.text(0.8, 0.91, '| '+cif_file.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='r', fontsize=10)
        elif mp_id is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id,final=False,structure=None,
                        str_file=None,label=None,scale=cif_scale,unit=unit,
                            marker='o',color='r',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9)  
            ax3.text(0.8, 0.91, '| '+mp_id.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='r', fontsize=10)

        if cif_file2 is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id,final=False,structure=None,
                        str_file=cif_file2,label=None,scale=cif_scale2,unit=unit,
                            marker='d',color='g',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9)
            ax3.text(0.8, 0.81, '| '+cif_file2.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='g', fontsize=10)
        elif mp_id2 is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id2,final=False,structure=None,
                        str_file=None,label=None,scale=cif_scale3,unit=unit,
                            marker='d',color='g',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9)        
            ax3.text(0.8, 0.81, '| '+mp_id2.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='g', fontsize=10)

        if cif_file3 is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id,final=False,structure=None,
                        str_file=cif_file3,label=None,scale=cif_scale2,unit=unit,
                            marker='d',color='b',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9)  
            ax3.text(0.8, 0.71, '| '+cif_file3.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='b', fontsize=10)
        elif mp_id3 is not None:
            xrd_plotter(ax=ax3,mp_id=mp_id3,final=False,structure=None,
                        str_file=None,label=None,scale=cif_scale3,unit=unit,
                            marker='d',color='b',label_yshift=0,label_xshift=0.1,radial_range=radial_range,
                            bottom=0,wl=ai.wavelength*10e9) 
            ax3.text(0.8, 0.71, '| '+mp_id3.split('/')[-1],verticalalignment='bottom', horizontalalignment='right', 
                     transform=ax3.transAxes, color='g', fontsize=10)


        if show_raw:
            i1d = ai.integrate1d(img,npt=npt, mask=None, method=method, 
                                    unit=unit, radial_range=radial_range)
            jupyter.plot1d(i1d,ax=ax3,label='Raw')
            ax3.set_xlabel(i1d_m.unit.label,loc='center')
        if median_filter_size > 1:
            jupyter.plot1d(i1d_m,ax=ax3,label='Median filtered and masked')
            ax3.set_xlabel(i1d_m.unit.label,loc='center')
        else:
            jupyter.plot1d(i1d_m,ax=ax3,label='Masked')
            ax3.set_xlabel(i1d_m.unit.label,loc='center')

        ax3.set_xlim(radial_range)
        ax3.set_title(None)

        if ylogscale:
            ax3.set_yscale('log')
            ax3.set_ylim(bottom=vmin)

        if xlogscale:
            ax3.set_xscale('log')
            ax2.set_xscale('log')

        if show_raw:
            ax3.legend(fontsize=8,loc=1)
        else:
            ax3.get_legend().remove()

        plt.tight_layout()

        if export_fig_as is not None:
            plt.savefig(export_fig_as,dpi=196)

    if export_xy_as is not None: 
        i1d = ai.integrate1d(img,npt,mask=mask,method=method,
                        filename=export_xy_as,unit='2th_deg')

    ds.attrs = {'ai':ai,
                'median_filter_size':median_filter_size,
                'npt':npt,
                'npt_azim':npt_azim,
                'method':method,
                'radial_range':radial_range,
                'unit':unit,
                'jupyter_style_plot':jupyter_style_plot,
                'robust':robust,
                'cmap':cmap,
                'vmin':vmin,
                'vmax':vmax,
                'plot':plot,
                'show_raw':show_raw,
                'xlogscale':xlogscale,  
                'ylogscale':ylogscale,  
                'export_xy_as':export_xy_as,                  
                'mp_id':mp_id,'mp_id2':mp_id2,'mp_id3':mp_id3,                   
                'cif_file':cif_file,  
                'cif_scale':cif_scale,
                'cif_file2':cif_file2,  
                'cif_scale2':cif_scale2,                
                'cif_file3':cif_file3,  
                'cif_scale3':cif_scale3,                
                'export_fig_as':export_fig_as
               }

    return ds