import calendar
import locale

from django.template.loader import render_to_string

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
calendar.LocaleHTMLCalendar(calendar.SUNDAY, 'pt_BR')


def criar_botao(req, mostrar):
    return render_to_string(
        template_name="lab/includes/calendario_button.html",
        context={"req": req, "mostrar": mostrar}
    )


class ReqCalendario(calendar.HTMLCalendar):

    def __init__(self, events=None, user=None):
        super(ReqCalendario, self).__init__()
        self.setfirstweekday(calendar.SUNDAY)
        self.events = events.order_by('hora_inicio')
        self.user = user

    def formatday(self, day, weekday, events):
        """
        Return a day as a table cell.
        """
        events_from_day = events.filter(data__day=day)
        events_html = '<div class="container-fluid" style="max-width: 15em">'
        for event in events_from_day:
            mostrar_completo = self.user.is_staff or event.professor == self.user
            events_html += criar_botao(event, mostrar_completo)
        events_html += '</div>'
        if day == 0:
            return '<td class="noday shadow">&nbsp;</td>'  # day outside month
        else:
            if len(events_from_day):
                day = '<strong>%s</strong>' % str(day)

            return '<td width="40px" height="60px" class="%s text-left shadow">%s%s</td>' % (
                self.cssclasses[weekday], str(day), events_html)

    def formatweek(self, theweek, events):
        """
        Return a complete week as a table row.
        """
        s = ''.join(self.formatday(d, wd, events) for (d, wd) in theweek)
        return '<tr>%s</tr>' % s

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="text-secondary shadow"><strong>%s<strong></tr>' % s

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a('<table class="table table-sm table-responsive-md table-bordered text-center shadow">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear).replace(
            '<tr>', '<tr class="gradiente">'))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week, self.events))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)
