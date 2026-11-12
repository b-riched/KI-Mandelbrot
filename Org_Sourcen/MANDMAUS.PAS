{ Maushandeling fÅr Mandelfa   }
{ Routinen entnommen aus Filer.pas, Tp 5.5 Bibliotheken }

program MandelfarbenPerMaus;

uses
  Graph,
  Crt,
  Dos,
  DosCall,
  BiosCall,
  Print2F,
  Strings,
  Mouse;

const
  Oben	    =	 8;	 { oberste Zeile im Datei-Bereich    }
  MaxUnten  =	25;	 { unterste Zeile im Datei-Bereich   }
  MaxDatei  =  800;	 { Max. verwaltete Dateianzahl	     }
  MaxAnf    =	28;	 { Max. Zeichenzahl je Dateianfang   }
  cTot	    = #254;	 { Marker nicht ansprechbare Datei   }
  cMark     = #175;	 { Markiert			     }
  cNotMark  = #249;	 { Nicht markiert		     }
  cWarte    =  500;	 { Wartezeit nach Programmeldungen   }

type
  tMenu     = record
		X,
		Y      : Byte;
		L      : Byte;
		B1     : Char;
		Txt    : String[20];
	      end;
			 { Typen fÅr Fensterverwaltung	     }
  tScreen   = array[0..79, 0..24] of Word;
  tRScreen  = record
		Scr    : tScreen;
		X,
		Y      : Byte;
	      end;
  tRScrPtr  = ^tRScreen;
  tWind     = record
		xo,yo,
		xu,yu  : Byte;
                color  : Byte;
	      end;

  tKBuffer  = array[1..MaxInt] of Char;

const
  MaxMenu   = 10;
  Menu	    : array[1..MaxMenu] of tMenu =
	      ((X : 0; Y : 0; L : 0; B1 : 'A';
		Txt : 'ttribut'),
	       (X : 0; Y : 0; L : 0; B1 : 'B';
		Txt : 'ewegen'),
	       (X : 0; Y : 0; L : 0; B1 : 'D';
		Txt : 'rucken'),
	       (X : 0; Y : 0; L : 0; B1 : 'H';
		Txt : 'ole DateianfÑnge'),
	       (X : 0; Y : 0; L : 0; B1 : 'K';
		Txt : 'opieren'),
	       (X : 0; Y : 0; L : 0; B1 : 'L';
		Txt : 'îschen'),
	       (X : 0; Y : 0; L : 0; B1 : 'M';
		Txt : 'arken zurÅcksetzen'),
	       (X : 0; Y : 0; L : 0; B1 : 'P';
		Txt : 'fad wechseln'),
	       (X : 0; Y : 0; L : 0; B1 : 'Q';
		Txt : 'uit'),
	       (X : 0; Y : 0; L : 0; B1 : 'U';
		Txt : 'mbenennen'));



var
  Idx,			 { Dateitabellenindex		     }
  IdxMax,		 { Max. Dateitabellenindex	     }
  Mi,			 { Position fÅr Maus		     }
  DosErr,		 { DosErrorspeicher		     }
  IOr,			 { IOresultspeicher		     }
  PosY, 		 { Position des Cursor am Bildschirm }
  Unten,		 { Unterste Dateieintragung	     }
  Hoehe      : Integer;  { Anzahl Zeilen		     }
  Summe      : LongInt;  { Anzahl der Zeichen aller Dateien  }
  Datei      : tDateiAr; { Dateitabelle 		     }
  Pfad, 		 { aktueller Pfad		     }
  NeuerPfad,		 { Pfad bei Pfadwechsel 	     }
  SaveDir,		 { Pfad beim Start		     }
  WinText    : String;	 { Text fÅr FensterÅberschrift	     }
  Screen1,		 { Speicher fÅr Bildschirminhalt     }
  Screen2,
  Screen3    : tRScrPtr;
  ScreenSeg  : Word;	 { Segmentadresse Bildschirm	     }
  SaveExit   : Pointer;  { TURBOs ExitProzedur		     }
  KBuffer    : ^tKBuffer;{ Buffer fÅr Dateioperationen	     }
  Ende	     : Boolean;  { Programmende 		     }


{ ------------------------- Unterprogramme ---------------------------------}


procedure SaveScreen (var Screen : tRScrPtr);

{ Bildschirminhalt sichern }
begin
  with Screen^ do
    begin
      X := WhereX;
      Y := WhereY;
      Move(Ptr(ScreenSeg, 0)^, Scr, SizeOf(tScreen));
    end;
end;


procedure RestoreScreen (var Screen : tRScrPtr);

{ Bildschirminhalt wiederherstellen }
begin
  with Screen^ do
    begin
      Move(Scr, Ptr(ScreenSeg, 0)^, SizeOf(tScreen));
      Window(1,1,80,25);
      GotoXY(X,Y);
    end;
end;


procedure Rahmen (Win : tWind);

{ Einen Rahmen um das Fenster zeichnen }
var
  i : Integer;
  tempoocolor : Byte;

begin
  with Win do
    begin
      Window(1,1,80,25);		  { zuerst die Ecken }
      GotoXY(xo,yo);
      Write(Form[1]);
      GotoXY(xu,yo);
      Write(Form[2]);
      GotoXY(xo,yu);
      Write(Form[3]);
      GotoXY(xu,yu);
      Write(Form[4]);

      GotoXY(xo+1,yo);				 { dann oben }
      Write(StrSet(Form[6],xu - xo - 1));
      GotoXY(xo+1,yu);			       { jetzt unten }
      Write(StrSet(Form[6],xu - xo - 1));

      for i:=1 to (yu - yo - 1) do
	begin			   { zuletzt die Senkrechten }
	  GotoXY(xo,yo+i);
	  Write(Form[5]);
	  GotoXY(xu,yo+i);
	  Write(Form[5]);
	end;

      if WinText <> ''			   { öberschrift ??? }
	then
	  begin
	    GotoXY(xo + ((xu - xo) -
		   Length(WinText) - 2) div 2,yo);
	    HighVideo;
	    Write(' '+WinText+' ');
	    LowVideo;
	  end;

      Window(xo+1,yo+1,xu-1,yu-1);
      ClrScr;
    end;
end;


function MouseKeyPressed : Boolean;

var
  esc	  : Char;
  b,a,x,y : Word;

begin
  esc := #0;
  b := 0;
  if KeyPressed
    then esc := ReadKey
    else if MouseOK
	   then GetMouseButtonPressed(b,a,x,y);
  MouseKeyPressed := ((esc <> #0) or (b > 0));
end;

procedure Fehler (Msg : String);

{ Fehler anzeigen }
var
  Txt	  : String;

begin
  SaveScreen(Screen3);
  Txt := Msg + ' Weiter mit <ESC> ';
  WinText := 'Fehler';
  Wind2.xu := Wind2.xo + Length(Txt) + 3;
  Rahmen(Wind2);
  Write(' ',Txt);
  ShowMouse;

  Sound(230);
  Delay(50);
  NoSound;

  repeat
  until MouseKeyPressed;

  HideMouse;
  RestoreScreen(Screen3);
end;


procedure Abbruch;

begin
  Idx := IdxMax;
  Sound(440);
  Delay(250);
  Sound(80);
  Delay(40);
  NoSound;
end;


procedure AlleMarken;

{ alle Marken zurÅcksetzen }
begin
  HideMouse;
  for Idx := 1 to IdxMax do
    begin
      with Datei[Idx] do
	begin
	  if Mark <> cTot
	    then if Mark = cMark
		   then Mark := cNotMark;
       end;
    end;

  ZeigeDateien(1);		    { neuen Zustand anzeigen }
  Idx := 1;
  PosY := Oben;
  ShowMouse;
  ZeigeOptionen;
end;


procedure ProcessKey;

{ was will die Frau, der Mann, das Kind, ...
  vor dem Computer von mir ??
}
var
  Ch1,
  Ch2	 : Char;
  Ma,
  Mb,
  Mx,
  My	 : Word;

   procedure TasteHome;

   begin
     ZeigeDateien(1);
     Idx := 1;
     Mi := 1;
     PosY := Oben;
   end;


   procedure TasteEnd;

   begin
     Idx := IdxMax - Hoehe + 1;
     if Idx < 1
       then Idx := 1;
     ZeigeDateien(Idx);
     Mi := Idx;
     Idx := IdxMax;
     PosY := Unten;
   end;


   procedure TasteUp;

   begin
     Dec(Idx);
     if Idx >= 1
       then
	 begin
	   if PosY > Oben
	     then Dec(PosY)
	     else
	       begin
		 GotoXY(1,Oben);
		 InsLine;
		 Schreibe(Idx);
		 Mi := Idx;
	       end;
	 end
       else
	 begin
	   Idx := 1;
	   Mi := Idx;
	 end;
   end;


   procedure TasteDown;

   begin
     Inc(Idx);
     if Idx <= IdxMax
       then
	 begin
	   if PosY < Unten
	     then Inc(PosY)
	     else
	       begin
		 GotoXY(1,Oben);
		 DelLine;
		 GotoXY(1,Unten);
		 Schreibe(Idx);
		 Mi := Idx -Hoehe + 1;
	       end;
	 end
       else
	 begin
	   Idx := IdxMax;
	   Mi := Idx - Hoehe + 1;
	 end;
   end;


   procedure Markieren;

   begin
     HideMouse;
     with Datei[Idx] do
       begin
	 if Mark <> cTot
	   then
	     begin
	       if Mark = cNotMark
		 then
		   begin
		     Mark := cMark;
		     HighVideo;
		   end
		 else Mark := cNotMark;
	       Write(Mark,' ',Name);
	       LowVideo;
	     end;
       end;
     ShowMouse;
   end;


   procedure PfadWechseln;

   var
     Lw    : Byte;
     VolID : String;

   begin
     HideMouse;
			     { CURrentSOuRce steht auf Verz. }
     if (Datei[Idx].Attr[2] = 'd') and (Datei[Idx].Name <> '.')
       then NeuerPfad := Pfad + Datei[Idx].Name
       else
	 begin		     { CURSOR steht nicht auf subdir }
	   SaveScreen(Screen2);
	   WinText := '';
	   Rahmen(Wind1);
	   Write(' Neuer Pfad ? ');
	   Readln(NeuerPfad);
	   NeuerPfad := UpString(NeuerPfad);
	   RestoreScreen(Screen2);
	 end;

	 if NeuerPfad = ''
	   then
	     begin
	       ZeigeOptionen;
	       ShowMouse;
	       exit;
	     end;

	 if ((NeuerPfad[1] in ['A'..'Z']) and (NeuerPfad[2] = ':'))
	   then Lw := Ord(NeuerPfad[1]) - 64
	   else Lw := GetDisk;
	 VolID := GetVolumeID(Lw);
	 DosErr := DosError;
	 if (DosErr = 152) or (DosErr = 3)
	   then
	     begin
	       Fehler('Laufwerk '+NeuerPfad+' nicht gefunden.');
	       ShowMouse;
	       ZeigeOptionen;
	       exit;
	     end;

     {$I-} ChDir(NeuerPfad); {$I+}	   { Pfad einstellen }
     IOr := IOresult;
     if IOr = 0
       then
	 begin
	   GetDir(0,Pfad);
	   if Pfad[Length(Pfad)] <> '\'
	     then Pfad := Pfad+'\';

	   Pfad := UpString(Pfad);
	   NeueListe;		    { neuen Zustand anzeigen }
	 end
       else Fehler('Pfad '+NeuerPfad+' nicht gefunden.');
     ShowMouse;
   end;


    procedure Mouse2Char (mb, mx, my : Word; var c1, c2 : Char);

    { Mausposition in Tastendruck umsetzen
    }
    var
      i : Integer;

    begin
      for i := 1 to MaxMenu do
	with Menu[i] do
	  begin
	    if my = Y
	      then if (mx >= X) and (mx <= (X + L))
		     then
		       begin
			 c1 := B1;
			 HideMouse;
			 GotoXY(X,Y);
			 HighVideo;
			 Write(B1,Txt);
			 LowVideo;
			 ShowMouse;
		       end;
	  end;

      if c1 = #255
	then
	  begin
	    if mx > 14
	      then
		begin
		  if (my = Unten) or (my = Unten - 1)
		    then
		      begin
			c1 := #0;
			c2 := #80;
		      end
		    else if my in [Oben - 1,Oben,Oben + 1]
			   then
			     begin
			       c1 := #0;
			       c2 := #72;
			     end;
		end
	      else
		begin
		  if (my >= Oben) and (my <= Unten)
		    then
		      begin
			PosY := My;
			Idx := Mi + My - Oben;
			HideMouse;
			GotoXY(1,PosY);
			ShowMouse;
			c1 := #32;
		      end;
	       end;
	  end;
    end;


begin
  Ch1 := #255;
  Ch2 := #255;
  Mb  := 0;

  if KeyPressed
    then
      begin
	Ch1 := ReadKey;
	if Ch1 = #0
	  then Ch2 := ReadKey
	  else Ch1 := UpCase(Ch1);
      end
    else
      begin
	if MouseOK
	  then
	    begin
	      Mb := 0;
	      GetMouseButtonPressed(Mb,Ma,Mx,My);
	      Mx := Trunc(Mx/8) + 1;
	      My := Trunc(My/8) + 1;
	      if Mb > 0
		then Mouse2Char(Mb,Mx,My,Ch1,Ch2);
	    end;
      end;

  case Ch1 of
     #0 : begin 			    { Funktionstaste }
	    HideMouse;
	    case Ch2 of
	      #71 : TasteHome;
	      #79 : TasteEnd;
	      #72 : TasteUp;
	      #80 : TasteDown;
	    end;
	    ShowMouse;
	  end;
    ' ' : begin
	    Markieren;
	    if Mb = 0
	      then
		begin
		  HideMouse;
		  TasteDown;
		  ShowMouse;
		end
	      else Delay(cWarte);  { Die Maus ist zu schnell }
	  end;
    'A' : Attribute;
    'B' : Bewegen;
    'D' : Drucken;
    'H' : DateiAnfang;
    'K' : Kopieren;
    'L' : Loeschen;
    'M' : AlleMarken;
    'P' : begin
	    PfadWechseln;
	    Delay(cWarte);
	  end;
    'Q' : Ende := true;
    'U' : Umbenennen;
  end;
end;


{ ------------------------------ Main --------------------------------------}

begin
  CheckBreak := false;


  GetMem(Screen1,SizeOf(tRScreen));
  GetMem(Screen2,SizeOf(tRScreen));
  GetMem(Screen3,SizeOf(tRScreen));
  GetMem(KBuffer,SizeOf(tKBuffer));

  Unten := MaxUnten;
  WinText := '';
  Ende := false;

  ResetMouse;
  SetTextCursor(1);
  ShowMouse;

  repeat				   { Eingabeschleife }
    GotoXY(1,PosY);
			{ Lesen der Anweisungen an den FILER }
    ProcessKey;
  until Ende;			     { bis zum bitteren Ende }

  HideMouse;
  RestoreScreen(Screen1);    { alten Bildschirminhalt zurÅck }

  FreeMem(Screen1,SizeOf(tRScreen));
  FreeMem(Screen2,SizeOf(tRScreen));
  FreeMem(Screen3,SizeOf(tRScreen));
  FreeMem(KBuffer,SizeOf(tKBuffer));
end.
