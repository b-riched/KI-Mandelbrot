{$N+,E-}
PROGRAM apfelbaeumchen;

{ -----------    Iteration der Konvergenzwerte   -----------

  nach SPEKTRUM DER WISSENSCHAFT, z := zx + i zy, c := cx + i cy,
  f(z) = zý + c, seite - Kantenl„nge des Grafikfensters, spalt - Entfernung
  zwischen zwei Pixeln, p - Anzahl der Pixel pro Achse
}

USES crt,graph;


{-----------------------------------------------------------------------------}


procedure mandel;

 const p = 480;
       zaehlermax = 1005;

 type  zeile = array[1..p] of integer;
 var   x,y,zaehler,nr                     : integer;
       seite_x,seite_y,zx,zy,cx,cy,hx,hy,
       xmax,xmin,ymax,ymin                : real;
       bild                               : zeile;
       datei                              : file of zeile;
       s                                  : string;

begin
   writeln;
   writeln('   Einlesen der Koordinaten  ');
   writeln;
   write  ('   xmin = ');  readln(xmin);
   write  ('   ymin = ');  readln(ymin);
   write  ('   xmax = ');  readln(xmax);
   write  ('   ymax = ');  readln(ymax);
   writeln;
   write  ('   lfd. Nr.: ');  readln(nr);
   str(nr,s);
   assign(datei,'e:\mandel'+ s +'.dat');
   rewrite(datei);

   bild[1] := trunc((xmin)*10000);
{  bild[2] := trunc(abs(xmin*10000-bild[1]));
}  bild[3] := trunc((xmax)*10000);
{  bild[4] := trunc(abs(frac(xmax*10000))*10);
}  bild[5] := trunc((ymin)*10000);
{  bild[6] := trunc(abs(frac(ymin*10000))*10);
}  bild[7] := trunc((ymax)*10000);
{  bild[8] := trunc(abs(frac(ymax*10000))*10);
}
   write(datei,bild);
   writeln;
   writeln('Programm  "Apfelb„umchen"  (mandelda.pas) l„uft.');
   writeln;
   seite_x := (xmax-xmin)/p;
   seite_y := (ymax-ymin)/p;

   for x := 1 to p do begin
      write(x,'  ');
      for y := 1 to p do begin
         cx := x * seite_x + xmin;
         cy := y * seite_y + ymin;
         zx := 0;
         zy := 0;
         zaehler := 0;
         while (((zx*zx+zy*zy) < 4) and (zaehler <= zaehlermax)) do begin
            hx := zx*zx - zy*zy + cx;
            hy := 2*zx*zy + cy;
            zx := hx;
            zy := hy;
            zaehler := zaehler + 1;
         end;
         bild[y] := zaehler;
      end; { for y }
      write(datei,bild);
   end; { for x }
   close(datei);
end; { mandel }


{--------------------------HAUPTPROGRAMM-------------------------------ä-------}


BEGIN
   clrscr;
   mandel;
   writeln;
   writeln('Weiter mit  RETURN');
   readln;
END.
{$N-,E+}

