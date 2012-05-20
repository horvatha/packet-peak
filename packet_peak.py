#!/usr/bin/env python

import sys
import apt_pkg

cache = None
type_recommends = 4

def count_pkg_revdepends(pkg):
	global cache

	rev_depends = 0
	for otherdep in pkg.rev_depends_list:
		if otherdep.parent_pkg.current_ver != None and \
				otherdep.parent_pkg.current_ver.id == otherdep.parent_ver.id and \
				(otherdep.dep_type_enum == apt_pkg.Dependency.TYPE_DEPENDS or \
				otherdep.dep_type_enum == apt_pkg.Dependency.TYPE_PREDEPENDS):
			rev_depends += 1
	if pkg.current_ver != None:
	  for provided in pkg.current_ver.provides_list:
		try:
			rev_depends += count_pkg_revdepends(cache[provided[0]])
		except KeyError as e:
			print "Package not found:",str(e).strip('"')

	return rev_depends

def is_available(pkg):
		if not pkg.has_versions:
			if pkg.has_provides:
				return True
			else:
				return False
		elif pkg.current_ver != None:
			return True
		else:
			return False


def dependencies(pkg, deps):

    if pkg.current_ver != None:
      for or_group in pkg.current_ver.depends_list.get("PreDepends", []) + \
                        pkg.current_ver.depends_list.get("Depends", []):
	for otherdep in or_group:
		if is_available(otherdep.target_pkg) and \
				count_pkg_revdepends(otherdep.target_pkg) == 1:
			deps.add(otherdep.target_pkg.id)
			dependencies(otherdep.target_pkg, deps)
    elif pkg.has_provides:
      for provider in pkg.provides_list:
	if is_available(provider[2].parent_pkg):
		deps.add(provider[2].parent_pkg.id)
		dependencies(provider[2].parent_pkg, deps)


def count_pkg_revrecommends(pkg):
	global type_recommends

	deps = set()
	deps.add(pkg.id)
	dependencies(pkg, deps)
	rev_recommends = 0
	for otherdep in pkg.rev_depends_list:
		if otherdep.parent_pkg.current_ver != None and \
				otherdep.parent_pkg.current_ver.id == otherdep.parent_ver.id and \
				otherdep.dep_type_enum == type_recommends and \
				not otherdep.parent_pkg.id in deps:
			rev_recommends += 1
	return rev_recommends

def list_orphans(orphans):
	global cache

	for otherpkg in cache.packages:
		if otherpkg.current_ver != None and not otherpkg.essential \
						and not otherpkg.important:
			if count_pkg_revdepends(otherpkg) == 0 and\
					count_pkg_revrecommends(otherpkg) == 0:
				orphans.append(otherpkg.name)

if __name__ == '__main__':
	apt_pkg.init()

	if apt_pkg.VersionCompare(apt_pkg.VERSION, "0.8") < 0:
		print "must use python-apt 0.8 or greater"
		sys.exit()

	if apt_pkg.Dependency.TYPE_RECOMMENDS != type_recommends:
		print "PYTHON-APT BUG: apt_pkg.Dependency.TYPE_RECOMMENDS is not equal to 4"

	cache = apt_pkg.Cache()

	print "List of orphan packages:"
	orphans = list()
	list_orphans(orphans)
	orphans.sort()
	print "\n".join(orphans)