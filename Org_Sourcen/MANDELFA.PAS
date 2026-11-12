{$N+}
{$E-}
PROGRAM mandelfarben;

 uses  mandpal,mouse,graph,crt,dos,mousewin;

 const p  = 480;
       xo = 159;
       pfad : string[16] = 'c:\tp\pasprog\';


 type  zeile = array[1..p] of integer;

 var   datei                     : file of Zeile;
       bild                      : zeile;
       i,x,y,zaehler,farbe,
       error                     : integer;
       s1,s2                     : string[12];
       wind                      : windtyp;           { global }
       xmin,xmax,ymin,ymax,                           { global }
       faktor,                                        { global }
       hilf                      : real;
       lfd_Nr                    : byte;
       PalettenNummer            : MPtype;


{------------------------------- Implementation ------------------------------}


procedure ScreenRight;
  var x,y : integer;
begin
    rectangle(0,0,getmaxx,getmaxy);
    x := getmaxx div 2 - 50;
    y := getmaxy div 2 - 50;
    rectangle(x,y,x+100,y+100);
    ReadLn;
    cleardevice;
end;


Procedure Bereichsangabe(xmin,ymin,xmax,ymax:real);
  var s1,s2 : string;
begin
   setlinestyle(0,0,1);
   setcolor(55);
   line(5,5,55,5);                    { x-Achse }
   outtextxy(60,10,'x');
   line(5,5,5,55);                    { y-Achse }
   outtextxy(10,60,'y');
   str(xmin:7:4,s1);
   str(xmax:7:4,s2);
   outtextxy(0,100,'X aus');
   setcolor(100);
   outtextxy(0,115,'[' + s1 + ',' + s2 + ']');
   str(ymin:7:4,s1);
   str(ymax:7:4,s2);
   setcolor(55);
   outtextxy(0,140,'Y aus');
   setcolor(100);
   outtextxy(0,155,'[' + s1 + ',' + s2 + ']');
end;


{-----------------------  H A U P T P R O G R A M M  -------------------------}


BEGIN
   clrscr;
   writeln('Mandel-Farben');
   writeln;
   write('Laufende Nummer: ');  readln(lfd_Nr);
   writeln;
   write('Nummer der Palette (0..',MaxPalette,'): ');
   readln(PalettenNummer);

   str(lfd_Nr,s1);
   assign(datei,pfad + 'm' + s1 + '.dat');
   reset(datei);
   read(datei,bild);

   xmin := bild[1]/10000; { + bild[2]/100000;  }
   xmax := bild[3]/10000; { + bild[4]/100000;  }
   ymin := bild[5]/10000; { + bild[6]/100000;  }
   ymax := bild[7]/10000; { + bild[8]/100000;  }

   faktor := (xmax-xmin)/p;

   InitializeGraphics;
   setfillstyle(0,0);
   setcolor(100);
   ScreenRight;
   SetTVGAPalette(PalettenNummer);

   x := 1;
   while not eof(datei) do begin
      read(datei,bild);
      farbe := bild[y];
      for y := 1 to p do putpixel(x+xo,y,bild[y]);
      inc(x);
   end;
   readln;

   with wind do begin
     po.x := xo;
     po.y := 0;
     pu.x := xo + p -1;
     pu.y := p -1;
   end;
   setcolor(100);
   Bereichsangabe(xmin,ymin,xmax,ymax);
   setcolor(0);
   auswahl(xmin,ymin,faktor,wind);
   close(datei);
   closegraph;
END.
{$N-}
{$E+}