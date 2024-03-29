import glob
import json
import os
import shutil
from datetime import datetime
from notebook.base.handlers import IPythonHandler

version_dir = './nb_versions/'

def index_versions():
    #! not in use currently
    """
    Search through custom local directory for historical versions and their info
    """
    fnames = glob.glob(version_dir+"*/*.ipynb", recursive=True)
    versions = [v.split('/')[-2] for v in fnames]

    tmp = []
    for f, v in zip(fnames, versions):
        time = last_modified_time(f)
        time_until_now = time_until_now(time)
        tmp.append(dict(fname=f, version=v, time=time,
                        time_until_now=time_until_now))
    tmp = sorted(tmp, key=lambda t: t['version'], reverse=True)

    with open(version_dir+'version_log.json', 'w') as fout:
        json.dump(tmp, fout)


def datetime_to_str(dt):
    """
    Convert default datetime format to str & remove digits after int part of seconds
    """
    result = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-7]
    return result


def last_modified_time(filename):
    #! not in use currently
    """
    Calculates the time when the file is last modified
    """
    t = os.path.getmtime(filename)
    # convert to datetime
    dt = datetime.fromtimestamp(t)
    return datetime_to_str(dt)


def time_until_now(strtime):
    #! not in use currently
    """
    Calculates how many months/d/h/m/s ago between given string datetime and now
    """
    def date_diff_in_seconds(dt2, dt1):
        diff = dt2 - dt1
        return diff.days * 24 * 3600 + diff.seconds

    def dhms_from_seconds(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        months, days = divmod(days, 30)
        return (months, days, hours, minutes, seconds)

    date1 = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    date2 = datetime.now()
    diff = dhms_from_seconds(date_diff_in_seconds(date2, date1))
    labels = ['months', 'd', 'h', 'm', 's']
    for i, _t in enumerate(diff):
        if _t > 0:
            label = f'{diff[i]} {labels[i]} ago'
            if i<=3:
                label = f'{diff[i+1]} {labels[i+1]} ago '
            else:
                label = f'{diff[i]} {labels[i]} ago'
        else:
            label = 'just now'
        break
    return label


class ChangeVersionHandler(IPythonHandler):
    """
    Copy over the selected version to the current working directory and overwrite
    """

    def get(self):
        version = self.get_query_argument('fname')
        self.write('Copying over the selected version')
        overwrite_version(version)
        
        self.write('works')


def overwrite_version(version):
    fname = version.split("/")[-1]
    current = "./"+fname
    shutil.copyfile(version, current)


class SaveLocallyHandler(IPythonHandler):
    """ 
    Creates a folder in the notebook's cwd called 'nv_versions', 
    each notebook version is saved inside a subfolder of name 
    'v-{version number}', eg. 'v-1','v-2'.
    """

    def get(self):
        if not os.path.isdir(version_dir):
            os.makedirs(version_dir, exist_ok=True)
        fpath = self.get_query_argument('fname')
        note = self.get_query_argument('note')
        fname = fpath.split("/")[-1]
        current = "./"+fname

        # assign incremental version number
        i = 1
        while os.path.exists(version_dir+f'{i}'):
            i += 1
        dir_for_new_version = version_dir + f'{i}' + '/'
        os.makedirs(dir_for_new_version, exist_ok=True)
        new = dir_for_new_version + fname
        shutil.copyfile(current, new)
        time_now = datetime_to_str(datetime.now())

        # write json with version info and version notes
        notebook_info = dict(fname=new, version=i, time=time_now, note=note)
        log_file = version_dir + 'version_log.json'
        if os.path.exists(log_file):
            with open(log_file, 'r') as fin:
                version_list = json.load(fin)['versions']
                version_list.append(notebook_info)
        else:
            version_list = [notebook_info]
        json_data = {'versions':version_list}
        with open(log_file, 'w') as fout:
            json.dump(json_data, fout)

        self.write('works')


        

