#!/usr/bin/perl

use strict;
no strict qw(refs);
use Benchmark qw(cmpthese);
use PDL;
use PDL::GSLSF::GAMMA;

use Inline C =>
  q{ double lgamma(double); },
  ENABLE => "AUTOWRAP";

our $A = 100;
our $B = 210;
our $a = 20;
our $b = 70;


my @subs = qw(hypergeom hypergeom_fast hypergeom_gsl hypergeom_gsl_2 hypergeom_c);

foreach my $sub (@subs)
{
  printf('%15.15s: %f'."\n", $sub, $sub->($A,$B,$a,$b));
}

cmpthese(30000,
         {
           map { $_ => "$_(\$A,\$B,\$a,\$b)" } @subs,
         },
       );


sub hypergeom
{
  my ($A, $B, $a, $b) = @_;

  return exp( (factln($A)+factln($B)+factln($a+$b)+factln($A+$B-$a-$b)) -
              (factln($A+$B)+factln($a)+factln($b)+factln($A-$a)+factln($B-$b)) );
}

sub factln
{
  return gammaln($_[0] + 1);
}

sub gammaln
{
  my $xx = shift;
  my @cof = (76.18009172947146, -86.50532032941677,
             24.01409824083091, -1.231739572450155,
             0.12086509738661e-2, -0.5395239384953e-5);
  my $y = my $x = $xx;
  my $tmp = $x + 5.5;
  $tmp -= ($x + .5) * log($tmp);
  my $ser = 1.000000000190015;
  for my $j (0..5) {
    $ser += $cof[$j]/++$y;
  }
  -$tmp + log(2.5066282746310005*$ser/$x);
}


sub hypergeom_fast
{
  my ($A, $B, $a, $b) = @_;

  return exp( (factln_f($A)+factln_f($B)+factln_f($a+$b)+factln_f($A+$B-$a-$b)) -
              (factln_f($A+$B)+factln_f($a)+factln_f($b)+factln_f($A-$a)+factln_f($B-$b)) );
}


sub factln_f
{
  my $x = (shift) + 1;
  my $tmp = $x + 5.5;
  $tmp -= ($x + .5) * log($tmp);
  my $ser = 1.000000000190015
         + 76.18009172947146    / ++$x
         - 86.50532032941677    / ++$x
         + 24.01409824083091    / ++$x
         -  1.231739572450155   / ++$x
         +  0.12086509738661e-2 / ++$x
         -  0.5395239384953e-5  / ++$x;
  return log(2.5066282746310005*$ser/($x-6)) - $tmp;
}


sub hypergeom_gsl
{
  my ($A, $B, $a, $b) = @_;

  return exp( ((gsl_sf_lnfact($A))[0]+(gsl_sf_lnfact($B))[0]+(gsl_sf_lnfact($a+$b))[0]+(gsl_sf_lnfact($A+$B-$a-$b))[0]) -
              ((gsl_sf_lnfact($A+$B))[0]+(gsl_sf_lnfact($a))[0]+(gsl_sf_lnfact($b))[0]+(gsl_sf_lnfact($A-$a))[0]+(gsl_sf_lnfact($B-$b))[0]) );
}


sub hypergeom_gsl_2
{
  my ($A, $B, $a, $b) = @_;

  my ($n0, $n1, $n2, $n3, $d0, $d1, $d2, $d3, $d4) = (pdl(),pdl(),pdl(),pdl(),pdl(),pdl(),pdl(),pdl(),pdl());

  gsl_sf_lnfact($A, $n0, undef);
  gsl_sf_lnfact($B, $n1, undef);
  gsl_sf_lnfact($a+$b, $n2, undef);
  gsl_sf_lnfact($A+$B-$a-$b, $n3, undef);
  gsl_sf_lnfact($A+$B, $d0, undef);
  gsl_sf_lnfact($a, $d1, undef);
  gsl_sf_lnfact($b, $d2, undef);
  gsl_sf_lnfact($A-$a, $d3, undef);
  gsl_sf_lnfact($B-$b, $d4, undef);

  return exp( $n0 + $n1 + $n2 + $n3 - $d0 - $d1 - $d2 - $d3 - $d4);
}


sub hypergeom_c
{
  my ($A, $B, $a, $b) = @_;

  return exp( (lgamma($A+1)+lgamma($B+1)+lgamma($a+$b+1)+lgamma($A+$B-$a-$b+1)) -
              (lgamma($A+$B+1)+lgamma($a+1)+lgamma($b+1)+lgamma($A-$a+1)+lgamma($B-$b+1)) );
}


