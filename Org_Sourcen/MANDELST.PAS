PROGRAM mandelstatistik;

{ ----------- Statistische Auswertung der Konvergenzwerte --------------- }

 uses  crt,dos;

 const p = 480;
       pfad  : string = 'c:\tp\pasprog\';


 type  zeile = array[1..p] of integer;

 var   datalt,datneu       : file of Zeile;
       werte               : array[0..1006] of longint;
       summen              : array[0..255] of integer;
       bildalt,bildneu     : zeile;
       i,x,y,zaehler       : integer;
       summe,schwelle      : longint;
       ch                  : char;
       xmin,xmax,ymin,ymax : real;
       stelle,rest         : word;
       s                   : string[3];
       lfd_Nr              : byte;


{-----------------------  H A U P T P R O G R A M M  -------------------------}


BEGIN

   clrscr;
   writeln('MandelStatistik');
   writeln;
   write('Laufende Nummer: ');  readln(lfd_Nr);
   str(lfd_Nr,s);
   assign(datalt,pfad + 'mandel' + s + '.dat');
   assign(datneu,pfad + 'm'      + s + '.dat');
   reset(datalt);
   rewrite(datneu);

   read(datalt,bildalt);
   xmin := bildalt[1]/10000;
   xmax := bildalt[3]/10000;
   ymin := bildalt[5]/10000;
   ymax := bildalt[7]/10000;

   for i := 0 to 1006 do werte[i] := 0;       { Verteilung der Abbruchwerte }

   summe := 0;
   while not eof(datalt) do begin
   inc(summe);
      read(datalt,bildalt);
      for x := 1 to p do inc(werte[bildalt[x]]);
   end;


   schwelle := (p*p-werte[0]-werte[1006]) div 1000;
   repeat
      zaehler := 0;
      summe := 0;
      for i := 0 to 255 do summen[i] := 0;
      for i := 1 to 1005 do begin
         summe := summe + werte[i];
         inc(summen[zaehler]);
         if (summe >= schwelle) or (i = 1005) then begin
            inc(zaehler);
            summe := 0;
         end;
      end;
      clrscr;
      summe := 0;
      for i := 0 to 255 do summe := summe + summen[i];

      if summe < 1005 then begin                          { Restverteilung }
        i := 0;
        rest := 1005-summe;
        repeat
          inc(summen[255-i],round(rest/2));
          inc(i);
          dec(rest,round(rest/2));
        until rest = 0;
      end;

      for i := 190 to 216 do begin
         write  (' Bereich ',i-1:2,': ',summen[i-1]:5);
         write  ('        Bereich ',i+19:2,': ',summen[i+19]:5);
         writeln('        Bereich ',i+39:2,': ',summen[i+39]:5);
      end;
      writeln;
      writeln('Schwellenwert: ',schwelle);
      writeln;
      writeln(' Weiter (+) oder neuer Schwellenwert (RETURN)');
      ch := readkey;
      if ch <> '+' then begin
         write('Neuer Schwellenwert: ');
         readln(schwelle);
      end;
   until ch = '+';
   writeln;
   writeln(' Bitte warten! ');

   reset(datalt);
   read(datalt,bildalt);
   write(datneu,bildalt);
   x := 1;
   while not eof(datalt) do begin
      read(datalt,bildalt);
      for y := 1 to p do begin
         stelle := 0;
         case bildalt[y] of 1..1005 : begin
                                      summe := 0;
                                      while not (summe >= bildalt[y]) do begin
                                         summe := summe + summen[stelle];
                                         inc(stelle);
                                      end;
                                   end;
         end; { case }
         bildneu[y] := stelle;
      end;   { for y }
      write(datneu,bildneu);
      inc(x);
   end;   { while not eof }
   close(datalt);
   close(datneu);
   clrscr;
END.