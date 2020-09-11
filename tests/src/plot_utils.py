import constants
import system_utils


def gnuplot(exe, *args):

  args_str = " ".join(args)
  cmd = "gnuplot -c {0}".format(exe, args_str)
  system_utils.call(cmd)
