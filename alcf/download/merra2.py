import os
from getpass import getpass
import requests
from alcf import misc

URS = b'urs.earthdata.nasa.gov'

TEMPLATE = {
	'M2I3NVASM': 'https://goldsmr5.gesdisc.eosdis.nasa.gov/daac-bin/OTF/HTTP_services.cgi?FILENAME=%2Fdata%2FMERRA2%2FM2I3NVASM.5.12.4%2F{year:04d}%2F{month:02d}%2FMERRA2_{gen}.inst3_3d_asm_Nv.{year:04d}{month:02d}{day:02d}.nc4&LABEL=MERRA2_{gen}.inst3_3d_asm_Nv.{year:04d}{month:02d}{day:02d}.SUB.nc&SERVICE=L34RS_MERRA2&DATASET_VERSION=5.12.4&FORMAT=bmM0Lw&VERSION=1.02&SHORTNAME=M2I3NVASM&BBOX={lat1:.3f}%2C{lon1:.3f}%2C{lat2:.3f}%2C{lon2:.3f}&VARIABLES=CLOUD%2CH%2CPHIS%2CPL%2CQI%2CQL%2CPS%2CT%2CQV%2CU%2CV',
	'M2I1NXASM': 'https://goldsmr4.gesdisc.eosdis.nasa.gov/daac-bin/OTF/HTTP_services.cgi?FILENAME=%2Fdata%2FMERRA2%2FM2I1NXASM.5.12.4%2F{year:04d}%2F{month:02d}%2FMERRA2_{gen}.inst1_2d_asm_Nx.{year:04d}{month:02d}{day:02d}.nc4&LABEL=MERRA2_{gen}.inst1_2d_asm_Nx.{year:04d}{month:02d}{day:02d}.SUB.nc&SERVICE=L34RS_MERRA2&DATASET_VERSION=5.12.4&FORMAT=bmM0Lw&VERSION=1.02&SHORTNAME=M2I1NXASM&BBOX={lat1:.3f}%2C{lon1:.3f}%2C{lat2:.3f}%2C{lon2:.3f}&VARIABLES=T2M%2CQV2M%2CTS',
	'M2T1NXFLX': 'https://goldsmr4.gesdisc.eosdis.nasa.gov/daac-bin/OTF/HTTP_services.cgi?FILENAME=%2Fdata%2FMERRA2%2FM2T1NXFLX.5.12.4%2F{year:04d}%2F{month:02d}%2FMERRA2_{gen}.tavg1_2d_flx_Nx.{year:04d}{month:02d}{day:02d}.nc4&BBOX={lat1:.3f}%2C{lon1:.3f}%2C{lat2:.3f}%2C{lon2:.3f}&FORMAT=bmM0Lw&SHORTNAME=M2T1NXFLX&LABEL=MERRA2_{gen}.tavg1_2d_flx_Nx.{year:04d}{month:02d}{day:02d}.SUB.nc&SERVICE=L34RS_MERRA2&VERSION=1.02&VARIABLES=FRSEAICE%2CPRECTOT%2CPRECTOTCORR&DATASET_VERSION=5.12.4',
	'M2T1NXRAD': 'https://goldsmr4.gesdisc.eosdis.nasa.gov/daac-bin/OTF/HTTP_services.cgi?FILENAME=%2Fdata%2FMERRA2%2FM2T1NXRAD.5.12.4%2F{year:04d}%2F{month:02d}%2FMERRA2_{gen}.tavg1_2d_rad_Nx.{year:04d}{month:02d}{day:02d}.nc4&SHORTNAME=M2T1NXRAD&SERVICE=L34RS_MERRA2&VARIABLES=LWTUP%2CSWTDN%2CSWTNT&BBOX={lat1:.3f}%2C{lon1:.3f}%2C{lat2:.3f}%2C{lon2:.3f}&LABEL=MERRA2_{gen}.tavg1_2d_rad_Nx.{year:04d}{month:02d}{day:02d}.SUB.nc&VERSION=1.02&DATASET_VERSION=5.12.4&FORMAT=nc4%2F',
}

def quote(s):
	return s.replace(b'\\', b'\\\\').replace(b'"', b'\\"')

def login(user=None, password=None, overwrite=False):
	if user is None:
		user = input('NASA Earthdata login: ')
	if password is None:
		password = getpass(prompt='NASA Earthdata password: ')
	if type(user) is not str:
		user = str(user)
	if type(password) is not str:
		password = str(password)

	home = os.path.expanduser("~")
	netrc = os.path.join(home, '.netrc')
	urs_cookies = os.path.join(home, '.urs_cookies')
	if os.name == 'nt':
		dodsrc = os.path.join(os.getcwd(), '.dodsrc')
	else:
		dodsrc = os.path.join(home, '.dodsrc')

	ask_files = [x for x in [netrc, urs_cookies, dodsrc] if os.path.exists(x)]
	if len(ask_files) > 0 and overwrite is False:
		print('The following files have to be overwritten:')
		for file_ in ask_files:
			print('    ' + file_)
		res = input('Continue [y/n]? ')
		if res != 'y':
			return

	with open(netrc, 'wb', opener=lambda p, f: os.open(p, f, mode=0o600)) as f:
		os.chmod(f.fileno(), 0o600)
		f.write(b'machine %s login "%s" password "%s"\n' % (
			URS,
			quote(user.encode('utf-8')),
			quote(password.encode('utf-8'))
		))
	misc.log_output(netrc)

	with open(urs_cookies, 'wb') as f:
		pass
	misc.log_output(urs_cookies)

	with open(dodsrc, 'wb') as f:
		f.write(b'HTTP.COOKIEJAR=%s\n' % os.fsencode(urs_cookies))
		f.write(b'HTTP.NETRC=%s\n' % os.fsencode(netrc))
	misc.log_output(dodsrc)

def download(output, product, year, month, day, lon1, lon2, lat1, lat2,
	nocache=False
):
	lon1_180 = lon1 if lon1 < 180 else lon1 - 360
	lon2_180 = lon2 if lon2 < 180 else lon2 - 360
	url = TEMPLATE[product].format(
		year=year, month=month, day=day,
		lat1=lat1, lat2=lat2,
		lon1=lon1_180, lon2=lon2_180,
		gen=(300 if year < 2011 else 400),
	)
	response = requests.get(url)
	with open(output, 'wb') as f:
		f.write(response.content)
