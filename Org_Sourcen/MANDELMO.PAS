PROGRAM fraktalbebilde;

{ z := zx + i zy, c := cx + i cy, f(z) = ,
  seite - Kantenl„nge des Grafikfensters, spalt - Entfernung
  zwischen zwei Pixeln, p - Anzahl der Pixel pro Achse
}

uses graph,crt;
var  graphdriver,graphmode : integer;
     palette               : palettetype;


PROCEDURE mandel;

 const p    =   400;
       xmin =  -5;
       xmax =   5;
       ymin =  -5;
       ymax =   5;
 type  zeile = array[1..p] of longint;
 var   x,y,zaehler,zaehlermax,i          : integer;
       seite_x,seite_y,zx,zy,cx,cy,hx,hy : real;
       farbe                             : 0..15;
       bild                              : zeile;
       datei                             : file of zeile;
       ch                                : char;
       s                                 : string[10];

begin
   zaehlermax := 50;
   cleardevice;
   for i := 0 to 10 do begin
      str(ymin+i*(ymax-ymin)*0.1:6:4,s);
      outtextxy(453,40*i,'- ');
      outtextxy(480,40*i,s);
      str(xmin+i*(xmax-xmin)*0.1:6:4,s);
      outtextxy(40*i+50,403,'|');
      settextstyle(0,1,0);
      outtextxy(40*i+58,422,s);
      settextstyle(0,0,0);
   end;
   seite_x := (xmax-xmin)/p;
   seite_y := (ymax-ymin)/p;

   for x := 1 to p do begin
      for y := 1 to p do begin
         cx :=  x * seite_x + xmin;
         cy :=  y * seite_y + ymin;
         zx := 1;
         zy := 1;
         zaehler := 0;
         while ((zx*zx+zy*zy) < 4) and (zaehler <= zaehlermax) do begin

hx := (cx*zx-cy*zy)/exp(sqr(sqr(zx))+sqr(sqr(zy))+4*sqr(zx)*zx*zy) +cx;

hy := (2*cy*zx*zy)/exp(6*sqr(zx)*sqr(zy)+4*zx*sqr(zy)*zy) +cy;

            zx := hx;
            zy := hy;
            zaehler := zaehler + 1;
         end;

         case zaehler of   0      : farbe :=  0;
                           1..  2 : farbe :=  4;
                           3..  4 : farbe := 14;
                           5..  6 : farbe := 15;
                           7..  8 : farbe :=  9;
                           9.. 10 : farbe := 11;
                          11.. 12 : farbe :=  5;
                          13.. 14 : farbe := 12;
                          15.. 16 : farbe :=  6;
                          17.. 18 : farbe :=  1;
                          19.. 20 : farbe := 13;
                          21.. 23 : farbe :=  3;
                          24.. 26 : farbe :=  7;
                          27.. 31 : farbe :=  2;
                          32.. 41 : farbe := 10;
                          42.. 50 : farbe :=  8;
                            51    : farbe :=  0;
         end; { case }
         putpixel(50+x,y,farbe);
      end;  { for y }
   end; { for x }
end; { mandel }

{--------------------------HAUPTPROGRAMM--------------------------------------}

BEGIN
   clrscr;
   graphdriver := detect;
   initgraph(graphdriver,graphmode,'\tp\graphics');
   getpalette(palette);
   mandel;
   outtextxy(480,450,'Weiter mit  RETURN');
   readln;
   closegraph;
END.

