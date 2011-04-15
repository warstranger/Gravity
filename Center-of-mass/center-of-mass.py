#!/usr/bin/env python3

import os, sys
from re import sub as re_sub

__author__ = 'warcraft.stranger@gmail.com'
__license__ = 'GPLv2'

def com_func(*points):
	"""Calculate coordinates of center-of-mass. Params:
	[(x1, y1, m1), (x2, y2, m2), ...]
	[(x1, y1, z1, m1), (x2, y2, z2, m2), ...], where is
	m1,m2 - masses, x1,y1,z1,x2,y2,z2 - coordinates.
	Return: [Xc, Yc, Mc] or [Xc, Yc, Zc, Mc] of center of mass
	"""

	mc = sum(map(lambda x: x[-1], points))
	ret = []
	for i in range(len(points[0]) - 1):
		ret.append(sum(map(lambda x: x[-1] * x[i], points)) / mc)
	ret.append(mc)
	return ret

def _get_masses_colors(masses):
	"""Return points colors depending on its masses"""

	# 7070FF -> 0000FF -> 0000A0 (light blue -> blue -> dark blue)
	colors_range = 95 + 113		# 208
	mass_min = min(masses)
	mass_range = max(masses) - mass_min
	# One graduation
	graduation = colors_range / mass_range
	# Transform points masses. Min mass => 0, max mass => masses range
	masses = [m - mass_min for m in masses]
	rgb_colors = []
	for mass in masses:
		color = int(mass * graduation)
		if color < 112:	color = '%02X%02XFF' % (112 - color, 112 - color)
		else:			color = '0000%02X' % (256 -(color -112))
		rgb_colors.append(color)
	return rgb_colors

def gen3d_gnuplot_files(cpoints, cm, base_name, rotate, comment):
	"""Generate script and data files for gnuplot
	<comment> - comment in the beginning of .dem file"""

	points_cnt = len(points)

	# Supports only positive coordinates
	x_min = 0; x_max = int(max(points)[0]) +1
	y_min = 0; y_max = int(max(map(lambda x: x[1], points))) +1
	z_min = 0; z_max = int(max(map(lambda x: x[2], points))) +1
	x_axis_max = x_max +1
	y_axis_max = y_max +1
	z_axis_max = z_max +1

	# Labels
	p_labels = []
	for n in range(len(points)):
		p_labels.append(
			'set label "%d" at first %.2f, first %.2f, first %.2f'\
				% (n +1, points[n][0], points[n][1], points[n][2],) +\
			' left front offset 1')
	# Points with color and legend for the splot command
	p_legends = []
	# Points colors depending on its masses
	p_colors = _get_masses_colors(list(map(lambda x: x[-1], points)))
	# Titles (legends) for points
	p_titles = []
	for n in range(len(points)):
		p_titles.append('%d - %.2f (%.2f; %.2f; %.2f)' % (n +1,
			points[n][-1], points[n][0], points[n][1], points[n][2]))
	# Append center of mass point
	p_titles.append('Cm - %.2f (%.2f; %.2f; %.2f)' %\
		(cm[-1], cm[0], cm[1], cm[2],))

	# Justify titles (legends)
	title_max_len = max(map(lambda x: len(x), p_titles))

	for n in range(len(points)):
		p_legends.append("'%s.dat' every ::%d::%d" % (base_name,
				points_cnt *6 +6 +n, points_cnt *6 +6 +n) +\
			' title "%s"' % p_titles[n].ljust(title_max_len) +\
			" with points lc rgb '#%s' pt 7 ps 2"	% p_colors[n])
	# Append center of mass point
	p_legends.append("'%s.dat' every ::%d::%d" % (base_name,
			points_cnt *7 +6, points_cnt *7 +6) +\
		' title "%s"' % p_titles[-1].ljust(title_max_len) +\
		" with points lc rgb 'black' pt 6 ps 2")

	# Help lines for splot command
	h_lines = []
	for n in range(len(points)):
		h_lines.append("'%s.dat' every ::%d::%d notitle with lines ls 1, \\"\
			% (base_name, n *6, n *6 +5))

	dem_file = '' if not comment else '# %s\n' % comment

	dem_file += '''
		set title "Center of mass"
		set lmargin 15
		set key on at screen 0.03, screen 1 left Left reverse
		set view 60, 110, 1, 1

		set xyplane at 0
		# Axis ranges
		set xrange[%d:%d]
		set yrange[%d:%d]
		set zrange[%d:%d]
		set border 4095 lt 0

		set xtics axis autofreq
		set ytics axis autofreq
		set ztics axis autofreq

		set mapping cartesian
		set grid xtics ytics noztics

		# Axis
		set arrow from %d,0,0 to %d,0,0 lt 2 lc rgb "#333333" head empty front
		set arrow from %d,0,0 to 0,%d,0 lt 2 lc rgb "#333333" head empty front
		set arrow from %d,0,0 to 0,0,%d lt 2 lc rgb "#333333" head empty front

		# Axis labels
		set xlabel "X" offset first %.2f
		set ylabel "Y" offset first 0, first %.2f
		set zlabel "Z" offset first 0, first 0, first %.2f

		# Help lines style for points
		set style line 1 lt 1 lc rgb '#90FF90' lw 1
		# Help line style for point of center of mass
		set style line 2 lt 4 lc rgb '#FFB600' lw 1

		# Points with labels
		%s
		set label "Cm" at first %.2f, first %.2f, first %.2f left front offset 1

		splot \\
			%s
			'%s.dat' every ::%d::%d title "" with lines ls 2, \\
			%s
		''' % (
			# axis ranges
			x_min, x_max, y_min, y_max, z_min, z_max,
			# axis
			x_min, x_axis_max, y_min, y_axis_max, z_min, z_axis_max,
			# axis labels
			x_max * .6, y_max * .6, z_max * .6,
			# points with labels
			'\n'.join(p_labels),
			# point of the center of mass and label
			cm[0], cm[1], cm[2],
			# help lines for points
			'\n'.join(h_lines),
			base_name, points_cnt *6, points_cnt *6 +5,
			# points colors and legends
			', \\\n'.join(p_legends)
		)

	if rotate:
		dem_file += '''
			# Defines for gnuplot.rot script
			limit_iterations = 360
			xrot = 60
			xrot_delta = 0
			zrot = 110
			zrot_delta = 1
			xview(xrot) = xrot
			zview(zrot) = zrot
			set view xview(xrot), zview(zrot), 1, 1
			set size square

			iteration_count = 0
			xrot = (xrot + xrot_delta)%360
			zrot = (zrot + zrot_delta)%360
			load "rotate.rot"
			'''

	dem_file += '\npause -1 "Press any key to quit"'

	# DAT file
	help_lines = []
	for n in range(len(points)):
		help_lines.append('''# Help lines for point %d
			%.2f 0 0
			%.2f %.2f 0
			0 %.2f 0
			%.2f %.2f 0
			%.2f %.2f 0
			%.2f %.2f %.2f''' % (n +1, points[n][0], points[n][0], points[n][1],
				points[n][1], points[n][0], points[n][1], points[n][0],
				points[n][1], points[n][0], points[n][1], points[n][2],))

	# Help line for the center of mass
	help_line_m = '''
			%.2f 0 0
			%.2f %.2f 0
			0 %.2f 0
			%.2f %.2f 0
			%.2f %.2f 0
			%.2f %.2f %.2f''' % (cm[0], cm[0], cm[1], cm[1], cm[0], cm[1],
				cm[0], cm[1], cm[0], cm[1], cm[2],)

	# Points coordinates
	p_coords = []
	for n in range(len(points)):
		p_coords.append('%.2f %.2f %.2f' % (points[n][0], points[n][1],
			points[n][2],))

	dat_file = '%s\n# Help lines\n%s' % (
		'\n'.join(help_lines), help_line_m.strip(),) +\
		'\n# Points and center of mass coordinates\n' + '\n'.join(p_coords) +\
		'\n%.2f %.2f %.2f' % (cm[0], cm[1], cm[2],)

	dem_file_lines = []
	for line in dem_file.strip().split('\n'):
		dem_file_lines.append(line.strip())
	del dem_file
	dat_file_lines = []
	for line in dat_file.strip().split('\n'):
		dat_file_lines.append(line.strip())
	del dat_file
	return ('\n'.join(dem_file_lines), '\n'.join(dat_file_lines),)

def print_usage():
	print ('Usage:\n  ./%s [-plot [-rotate] [-base <name>]] <p1> <p2> [<p3>..<pN>]'\
			% os.path.basename(sys.argv[0]) +\
		'\n    <p1>..<pN>: points in format <x,y,z,m> or <x,y,m>' +\
		' (x,y,z - coordinates, m - mass)' +\
		'\n    -plot: generate script and data files for gnuplot' +\
		' (only 3D)' +\
		'\n    -rotate: rotate result by 360 degrees dymanimcally' +\
		'\n    -base <name>: save files for the gnuplot program with' +\
		' names <name>.dem and <name>.dat (default "custom")\n')

def print_examples():
	print ('Examples:')
	print ('  ./%s' % os.path.basename(sys.argv[0]) +\
		' 2,1,6 3,7,5 4,3,2 - calculate mass and coordinates (x,y) of' +\
		' center of mass\n\t1st point is (2;1) with mass 6\n' +\
		'\t2nd point is (3;7) with mass 5\n' +\
		'\t3rd point is (4;3) with mass 2\n')
	print ('  ./%s' % os.path.basename(sys.argv[0]) +\
		' 4.0,5.0,2,2 1,6,5,3 3,2,3,4 - calculate mass and coordinates' +\
		' (x,y,z) of center of mass\n' +\
		'\t1st point (4,0;5,0;2) with mass 2\n' +\
		'\t2nd point is (1;6;5) with mass 3\n' +\
		'\t3rd point is (3;2;3) with mass 4\n')

def _check_opts(args):
	for opt in ['-plot', '-rotate', '-base']:
		if args.count(opt) >1:
			return (1, 'Only one "%s" option can be specified' % opt)
	if '-base' in args and '-plot' not in args:
		return (1,
			'For the "-base" option you must specify "-plot" option as well')
	if '-rotate' in args and '-plot' not in args:
		return (1,
			'For the "-rotate" option you must specify "-plot" option as well')
	if '-base' in args:
		b_ind = args.index('-base')
		if len(args) < (b_ind +2) or args[b_ind +1] in ['-plot', '-rotate']:
			return (1, 'Specify <name> for the "-base" option')
	return 0, ''

def _get_opts(args):
	"""Get options for the gnuplot scripts and remove them from arguments"""

	opts = ()
	plot3d = 1 if '-plot' in args else 0
	rotate3d = 1 if '-rotate' in args else 0
	base_name = 'custom'

	if '-plot' in args:
		args.remove('-plot')
	if '-rotate' in args:
		args.remove('-rotate')
	if '-base' in args:
		base_ind = args.index('-base')
		args.remove('-base')
		base_name = args.pop(base_ind)

	return (args, plot3d, rotate3d, base_name)


if __name__ == '__main__':
	# Check options rightness
	q, msg = _check_opts(sys.argv[1:])
	if q:
		print (msg)
		sys.exit(1)
	del q, msg

	script = os.path.basename(sys.argv[0])
	args, plot3d, rotate3d, base_name = _get_opts(sys.argv[1:])

	if not args:
		print_usage()
		print_examples()

	elif len(args) <2:
		print ('Please specify at least 2 points\n')
		print_usage()
		print_examples()

	else:
		points = []
		coords_col = len(args[0].split(',')) -1

		if coords_col not in [2, 3]:
			print ('Error in coordinates of point 1')
			sys.exit(1)

		n = 0
		for arg in args:
			n += 1
			col = len(arg.split(',')) -1
			if col != coords_col:
				print ('Error in coordinates of point %d' % n)
				sys.exit()
			parts = [p.strip() for p in arg.split(',')]
			check_def = lambda x: not x or re_sub('[0-9]', '',
				x.replace('.', '', 1))
			if any(map(check_def, parts)):
				print ('Error in coordinates of point %d' % n)
				sys.exit()
			points.append(tuple([float(f) for f in parts]))

		print ('Points:')
		n = 0
		for p in points:
			n += 1
			if coords_col == 2:
				print ('  %d - mass %f, coordinates (%f; %f)' \
					% (n, p[2], p[0], p[1],))
			else:
				print ('  %d - mass %f, coordinates (%f; %f; %f)' \
					% (n, p[3], p[0], p[1], p[2],))

		if coords_col == 2:
			xc, yc, mc = com_func(*points)
			print ('Center of mass is (%f; %f) with mass %f' % (xc, yc, mc))
		else:
			xc, yc, zc, mc = com_func(*points)
			print ('Center of mass is (%f; %f; %f) with mass %f'\
				% (xc, yc, zc, mc))

		if plot3d and coords_col == 3:
			comment = './%s -plot%s "%s"' % (script,
				' -rotate' if rotate3d else '', '" "'.join(args))
			dem_file, dat_file = gen3d_gnuplot_files(points,
				[xc, yc, zc, mc], base_name, rotate3d, comment)
			f = open('%s.dem' % base_name, 'w+')
			f.write(dem_file)
			f.close()
			f = open('%s.dat' % base_name, 'w+')
			f.write(dat_file)
			f.close()

			print ('To start visualization run: gnuplot %s.dem' % base_name)
